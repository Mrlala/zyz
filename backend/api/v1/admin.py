"""后台管理接口

对应 SDD 4.5.12（接口 25-33）：
- GET /admin/words：词条管理列表
- PUT /admin/words/{word_id}：修改词条
- DELETE /admin/words/{word_id}：删除词条
- PUT /admin/words/{word_id}/risk：标记风险
- GET /admin/submissions：待审核列表
- PUT /admin/submissions/{submission_id}/review：审核提交
- GET /admin/stats：数据统计
- GET /admin/corrections：纠错列表
- PUT /admin/corrections/{correction_id}/review：审核纠错
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_admin_user
from core.database import get_db
from models.category import Category
from models.feedback import Feedback
from models.submission import CorrectionReport, Submission
from models.user import User
from models.word import Word
from schemas import BaseResponse
from services.word_service import WordService

router = APIRouter(prefix="/admin", tags=["后台管理"])


# ---- 请求模型 ----

class WordUpdateRequest(BaseModel):
    """修改词条请求。"""

    definition: str | None = None
    tags: list[str] | None = None
    category_id: int | None = None


class RiskUpdateRequest(BaseModel):
    """标记风险请求。"""

    risk_level: str = Field(..., description="风险等级：low/medium/high")
    risk_types: list[str] = Field(default_factory=list)
    advice: str = ""


class ReviewRequest(BaseModel):
    """审核请求。"""

    action: str = Field(..., description="审核动作：approve/reject")
    comment: str | None = None
    meaning: str | None = Field(None, description="审核通过时可选：覆盖提交的释义（D13）")


# ---- 词条管理 ----

@router.get("/words", response_model=BaseResponse)
async def admin_list_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status", description="normal/flagged/hidden"),
    risk_level: str | None = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """词条管理列表。"""
    query = select(Word).where(Word.deleted_at.is_(None))
    if keyword:
        query = query.where(Word.word.like(f"%{keyword}%"))
    if status_filter:
        # normal → published, flagged → pending, hidden → rejected
        status_map = {"normal": "published", "flagged": "pending", "hidden": "rejected"}
        db_status = status_map.get(status_filter)
        if db_status:
            query = query.where(Word.status == db_status)
    if risk_level:
        query = query.where(Word.risk_level == risk_level)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = query.order_by(Word.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    words = db.execute(query).scalars().all()

    items = [
        {
            "id": w.id,
            "word": w.word,
            "status": w.status,
            "risk_level": w.risk_level,
            "view_count": w.view_count,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in words
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.put("/words/{word_id}", response_model=BaseResponse)
async def admin_update_word(
    word_id: int,
    request: WordUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """修改词条。"""
    service = WordService()
    fields: dict = {}
    if request.definition is not None:
        fields["meaning"] = request.definition
    if request.tags is not None:
        fields["risk_types"] = request.tags
    if request.category_id is not None:
        fields["category_id"] = request.category_id

    try:
        word = service.update(word_id, db, **fields)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return BaseResponse(data={
        "id": word.id,
        "updated_at": word.updated_at.isoformat() if word.updated_at else None,
    })


@router.delete("/words/{word_id}", response_model=BaseResponse)
async def admin_delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """删除词条（软删除）。"""
    service = WordService()
    try:
        service.delete(word_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return BaseResponse(data={
        "id": word_id,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    })


@router.put("/words/{word_id}/risk", response_model=BaseResponse)
async def admin_update_risk(
    word_id: int,
    request: RiskUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """标记词条风险。"""
    if request.risk_level not in ("low", "medium", "high"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="risk_level 取值非法",
        )

    word = db.get(Word, word_id)
    if word is None or word.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="词条不存在")

    word.risk_level = request.risk_level
    word.risk_types = request.risk_types
    word.risk_advice = request.advice
    db.commit()

    return BaseResponse(data={
        "id": word.id,
        "risk_level": word.risk_level,
        "risk_types": word.risk_types,
        "updated_at": word.updated_at.isoformat() if word.updated_at else None,
    })


# ---- 提交审核 ----

@router.get("/submissions", response_model=BaseResponse)
async def admin_list_submissions(
    status_filter: str = Query("pending", alias="status", description="pending/approved/rejected"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """待审核提交列表。"""
    if status_filter not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status 取值非法")

    query = select(Submission).where(Submission.status == status_filter)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = query.order_by(Submission.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    submissions = db.execute(query).scalars().all()

    # 批量查询提交者信息
    user_ids = {s.user_id for s in submissions}
    users = {
        u.id: u
        for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()
    } if user_ids else {}

    items = [
        {
            "submission_id": s.id,
            "word": s.word,
            "definition": s.meaning,
            "submitter": (
                {"user_id": users[s.user_id].id, "nickname": users[s.user_id].nickname or users[s.user_id].username}
                if s.user_id in users else None
            ),
            "status": s.status,
            "submitted_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in submissions
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.put("/submissions/{submission_id}/review", response_model=BaseResponse)
async def admin_review_submission(
    submission_id: int,
    request: ReviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """审核用户提交。"""
    if request.action not in ("approve", "reject"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="action 取值非法")

    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交不存在")
    if submission.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已审核")

    new_status = "approved" if request.action == "approve" else "rejected"
    submission.status = new_status
    submission.reviewer_id = admin.id
    submission.reviewed_at = datetime.now(timezone.utc)
    # 保存审核评论：拒绝时通常用于记录驳回原因，通过时如有备注也一并保存
    if request.comment:
        submission.review_comment = request.comment

    word_id = None
    # 审核通过则创建正式词条（D13：审核员可通过 meaning 字段覆盖提交的释义）
    if new_status == "approved":
        new_word = Word(
            word=submission.word,
            meaning=request.meaning or submission.meaning,
            example=submission.example,
            category_id=submission.category_id,
            status="published",
            source="manual",
            created_by=submission.user_id,
        )
        db.add(new_word)
        db.flush()
        word_id = new_word.id

    db.commit()

    return BaseResponse(data={
        "submission_id": submission.id,
        "status": new_status,
        "word_id": word_id,
        "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
    })


# ---- 数据统计 ----

@router.get("/stats", response_model=BaseResponse)
async def admin_stats(
    start_date: str | None = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="截止日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """数据统计。"""
    word_count = db.execute(
        select(func.count(Word.id)).where(Word.deleted_at.is_(None))
    ).scalar_one()
    user_count = db.execute(select(func.count(User.id))).scalar_one()
    # 统计今日翻译次数
    from models.translation import Translation
    translation_count_today = db.execute(
        select(func.count(Translation.id)).where(
            func.date(Translation.created_at) == func.current_date()
        )
    ).scalar_one()
    feedback_pending = db.execute(
        select(func.count(Feedback.id))
    ).scalar_one()
    submission_pending = db.execute(
        select(func.count(Submission.id)).where(Submission.status == "pending")
    ).scalar_one()
    correction_pending = db.execute(
        select(func.count(CorrectionReport.id)).where(CorrectionReport.status == "pending")
    ).scalar_one()

    # 热词 Top
    hot_words = (
        db.execute(
            select(Word)
            .where(Word.status == "published", Word.deleted_at.is_(None))
            .order_by(Word.view_count.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    hot_top = [
        {"id": w.id, "word": w.word, "heat": w.view_count or 0}
        for w in hot_words
    ]

    return BaseResponse(data={
        "word_count": word_count,
        "user_count": user_count,
        "translation_count_today": translation_count_today,
        "feedback_count_pending": feedback_pending,
        "submission_count_pending": submission_pending,
        "correction_count_pending": correction_pending,
        "hot_top": hot_top,
    })


# ---- 纠错审核 ----

@router.get("/corrections", response_model=BaseResponse)
async def admin_list_corrections(
    status_filter: str = Query("pending", alias="status", description="pending/approved/rejected"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """纠错列表。"""
    if status_filter not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status 取值非法")

    query = select(CorrectionReport).where(CorrectionReport.status == status_filter)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = query.order_by(CorrectionReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    corrections = db.execute(query).scalars().all()

    # 批量查询词条与提交者
    word_ids = {c.word_id for c in corrections}
    user_ids = {c.user_id for c in corrections}
    words = {
        w.id: w
        for w in db.execute(select(Word).where(Word.id.in_(word_ids))).scalars().all()
    } if word_ids else {}
    users = {
        u.id: u
        for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars().all()
    } if user_ids else {}

    items = [
        {
            "correction_id": c.id,
            "word_id": c.word_id,
            "word": words[c.word_id].word if c.word_id in words else "",
            "type": c.type,
            "content": c.content,
            "submitter": (
                {"user_id": users[c.user_id].id, "nickname": users[c.user_id].nickname or users[c.user_id].username}
                if c.user_id in users else None
            ),
            "status": c.status,
            "submitted_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in corrections
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.put("/corrections/{correction_id}/review", response_model=BaseResponse)
async def admin_review_correction(
    correction_id: int,
    request: ReviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    """审核纠错。"""
    if request.action not in ("approve", "reject"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="action 取值非法")

    correction = db.get(CorrectionReport, correction_id)
    if correction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="纠错记录不存在")
    if correction.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已审核")

    correction.status = "approved" if request.action == "approve" else "rejected"
    db.commit()

    return BaseResponse(data={
        "correction_id": correction.id,
        "status": correction.status,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    })
