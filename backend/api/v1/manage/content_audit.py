"""内容审核接口（后台）

- GET /audit/submissions：用户提交列表（分页，筛选 status）
- PUT /audit/submissions/{id}/review：审核提交（approve/reject）
- GET /audit/corrections：纠错列表（分页，筛选 status）
- PUT /audit/corrections/{id}/review：审核纠错

权限点：content:submission:audit、content:correction:audit
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount
from models.submission import CorrectionReport, Submission
from models.user import User
from models.word import Word
from schemas import BaseResponse

router = APIRouter(prefix="/audit", tags=["内容审核"])


# ---- 请求模型 ----

class ReviewRequest(BaseModel):
    """审核请求。"""

    action: str = Field(..., description="approve/reject")
    comment: str | None = None
    meaning: str | None = Field(None, description="审核通过时可选：覆盖释义")


# ---- 提交审核 ----

@router.get("/submissions", response_model=BaseResponse)
async def list_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str = Query("pending", alias="status", description="pending/approved/rejected"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:submission:audit")),
) -> BaseResponse:
    """用户提交列表。"""
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
            "id": s.id,
            "user_id": s.user_id,
            "word": s.word,
            "meaning": s.meaning,
            "example": s.example,
            "category_id": s.category_id,
            "status": s.status,
            "vote_count": s.vote_count,
            "submitter": (
                {
                    "user_id": users[s.user_id].id,
                    "username": users[s.user_id].username,
                    "nickname": users[s.user_id].nickname or users[s.user_id].username,
                }
                if s.user_id in users else None
            ),
            "reviewer_id": s.reviewer_id,
            "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None,
            "review_comment": s.review_comment,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in submissions
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.put("/submissions/{submission_id}/review", response_model=BaseResponse)
async def review_submission(
    submission_id: int,
    body: ReviewRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:submission:audit")),
) -> BaseResponse:
    """审核用户提交。

    approve 时可选通过 meaning 覆盖释义，并创建正式 Word（status=published, source=manual）。
    """
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="action 取值非法")

    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提交不存在")
    if submission.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已审核")

    new_status = "approved" if body.action == "approve" else "rejected"
    submission.status = new_status
    submission.reviewer_id = admin.id
    submission.reviewed_at = datetime.now(timezone.utc)
    if body.comment:
        submission.review_comment = body.comment

    word_id = None
    if new_status == "approved":
        new_word = Word(
            word=submission.word,
            meaning=body.meaning or submission.meaning,
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
        "id": submission.id,
        "status": new_status,
        "word_id": word_id,
        "reviewer_id": submission.reviewer_id,
        "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
    })


# ---- 纠错审核 ----

@router.get("/corrections", response_model=BaseResponse)
async def list_corrections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str = Query("pending", alias="status", description="pending/approved/rejected"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:correction:audit")),
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
            "id": c.id,
            "word_id": c.word_id,
            "word": words[c.word_id].word if c.word_id in words else "",
            "user_id": c.user_id,
            "type": c.type,
            "content": c.content,
            "status": c.status,
            "submitter": (
                {
                    "user_id": users[c.user_id].id,
                    "username": users[c.user_id].username,
                    "nickname": users[c.user_id].nickname or users[c.user_id].username,
                }
                if c.user_id in users else None
            ),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in corrections
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.put("/corrections/{correction_id}/review", response_model=BaseResponse)
async def review_correction(
    correction_id: int,
    body: ReviewRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:correction:audit")),
) -> BaseResponse:
    """审核纠错。"""
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="action 取值非法")

    correction = db.get(CorrectionReport, correction_id)
    if correction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="纠错记录不存在")
    if correction.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已审核")

    correction.status = "approved" if body.action == "approve" else "rejected"
    correction.reviewer_id = admin.id
    correction.reviewed_at = datetime.now(timezone.utc)
    if body.comment:
        correction.review_comment = body.comment
    db.commit()

    return BaseResponse(data={
        "id": correction.id,
        "status": correction.status,
        "reviewer_id": correction.reviewer_id,
        "reviewed_at": correction.reviewed_at.isoformat() if correction.reviewed_at else None,
        "review_comment": correction.review_comment,
    })
