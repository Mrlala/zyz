"""用户提交接口

对应 SDD 4.5.11：
- POST /submissions：提交新词条
- GET /submissions：我的提交列表
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_required
from core.database import get_db
from models.category import Category
from models.submission import Submission
from models.user import User
from models.word import Word
from schemas import BaseResponse, SubmissionRequest

router = APIRouter(prefix="/submissions", tags=["用户提交"])


@router.post("", response_model=BaseResponse)
async def create_submission(
    request: SubmissionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """提交新词条（进入 pending 队列等待审核）。"""
    # 校验词条是否已存在
    existing = db.execute(
        select(Word).where(Word.word == request.word, Word.deleted_at.is_(None))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="词条已存在",
        )

    # 校验分类存在
    if request.category_id is not None:
        category = db.get(Category, request.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="分类不存在",
            )

    submission = Submission(
        user_id=user.id,
        word=request.word,
        meaning=request.definition,
        example=request.example,
        category_id=request.category_id or 0,
        status="pending",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return BaseResponse(data={
        "submission_id": submission.id,
        "status": submission.status,
        "submitted_at": submission.created_at.isoformat() if submission.created_at else None,
    })


@router.get("", response_model=BaseResponse)
async def list_my_submissions(
    status_filter: str | None = Query(None, alias="status", description="按状态筛选：pending/approved/rejected"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """获取我的提交列表。"""
    if status_filter is not None and status_filter not in ("pending", "approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status 取值非法",
        )

    query = select(Submission).where(Submission.user_id == user.id)
    if status_filter is not None:
        query = query.where(Submission.status == status_filter)

    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()

    query = (
        query.order_by(Submission.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    submissions = db.execute(query).scalars().all()

    items = [
        {
            "submission_id": s.id,
            "word": s.word,
            "status": s.status,
            "submitted_at": s.created_at.isoformat() if s.created_at else None,
            "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None,
            "review_comment": None,
        }
        for s in submissions
    ]

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
