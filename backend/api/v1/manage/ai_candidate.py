"""AI 候选词管理接口（后台）

- GET /manage/ai-candidates：候选词列表（分页 + 状态/频次筛选 + 关键词搜索）
- POST /manage/ai-candidates/{id}/promote：手动转为 Submission
- DELETE /manage/ai-candidates/{id}：丢弃候选词

权限点：content:word:manage
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount
from models.ai_candidate import AiWordCandidate
from models.category import Category
from models.submission import Submission
from schemas import BaseResponse

router = APIRouter(prefix="/ai-candidates", tags=["AI 候选词"])


@router.get("", response_model=BaseResponse)
async def list_ai_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status", description="状态：collecting/promoted/discarded"),
    min_count: int | None = Query(None, ge=1, description="最小出现频次"),
    keyword: str | None = Query(None, description="候选词关键词搜索"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """AI 候选词列表。"""
    query = select(AiWordCandidate)
    if status_filter:
        query = query.where(AiWordCandidate.status == status_filter)
    if min_count is not None:
        query = query.where(AiWordCandidate.occurrence_count >= min_count)
    if keyword:
        query = query.where(AiWordCandidate.word.like(f"%{keyword}%"))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = (
        query.order_by(AiWordCandidate.occurrence_count.desc(), AiWordCandidate.last_seen_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(query).scalars().all()

    items = [
        {
            "id": c.id,
            "word": c.word,
            "meaning": c.meaning,
            "context_sample": c.context_sample,
            "occurrence_count": c.occurrence_count,
            "status": c.status,
            "promoted_submission_id": c.promoted_submission_id,
            "first_seen_at": c.first_seen_at.isoformat() if c.first_seen_at else None,
            "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in rows
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.post("/{candidate_id}/promote", response_model=BaseResponse)
async def promote_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """手动将候选词转为 Submission（即使频次未达阈值）。"""
    candidate = db.get(AiWordCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选词不存在")
    if candidate.status == "promoted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该候选词已转提交")
    if candidate.status == "discarded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该候选词已丢弃，无法转提交")

    # 获取默认分类
    default_category = db.execute(select(Category).limit(1)).scalar_one_or_none()
    if default_category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无分类数据，无法创建 Submission")

    # 取最后一次释义
    meaning = candidate.meaning or "AI 自动补充词条"
    if "---" in meaning:
        meaning = meaning.split("---")[-1].strip()

    submission = Submission(
        user_id=None,
        word=candidate.word,
        meaning=meaning,
        category_id=default_category.id,
        status="pending",
    )
    db.add(submission)
    db.flush()
    candidate.status = "promoted"
    candidate.promoted_submission_id = submission.id
    db.commit()

    return BaseResponse(data={
        "candidate_id": candidate.id,
        "submission_id": submission.id,
        "word": candidate.word,
        "status": "promoted",
    })


@router.delete("/{candidate_id}", response_model=BaseResponse)
async def discard_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """丢弃候选词（status=discarded，不删除记录）。"""
    candidate = db.get(AiWordCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="候选词不存在")
    if candidate.status == "promoted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该候选词已转提交，无法丢弃",
        )
    candidate.status = "discarded"
    db.commit()
    return BaseResponse(data={"candidate_id": candidate.id, "status": "discarded"})
