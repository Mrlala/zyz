"""反馈接口

对应 SDD 4.5.9：
- POST /feedback：提交质量反馈
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_required, get_device_id
from core.database import get_db
from core.sensitive_filter import contains_sensitive, is_sensitive_filter_enabled
from models.feedback import Feedback
from models.user import User
from schemas import BaseResponse, FeedbackRequest
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["反馈"])


@router.post("", response_model=BaseResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
    device_id: str | None = Depends(get_device_id),
) -> BaseResponse:
    """提交质量反馈。

    - accurate：词条置信度权重 +1
    - inaccurate：创建纠错记录
    - outdated：词条标记待复审
    """
    if request.type not in ("accurate", "inaccurate", "outdated"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="type 取值非法，仅支持 accurate/inaccurate/outdated",
        )

    # 敏感词过滤：检查补充说明
    if is_sensitive_filter_enabled() and request.comment and contains_sensitive(request.comment):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="反馈内容包含敏感词，请修改后重试",
        )

    service = FeedbackService()
    try:
        result = service.submit(
            translation_id=request.translation_id,
            feedback_type=request.type,
            comment=request.comment,
            user_id=user.id,
            device_id=device_id,
            db=db,
        )
    except ValueError as exc:
        msg = str(exc)
        if "不存在" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "已" in msg:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # 查询刚创建的反馈 ID
    feedback = db.execute(
        select(Feedback)
        .where(
            Feedback.translation_id == request.translation_id,
            Feedback.user_id == user.id,
        )
        .order_by(Feedback.id.desc())
    ).scalars().first()

    return BaseResponse(data={
        "success": True,
        "message": "反馈成功",
        "feedback_id": feedback.id if feedback else 0,
    })
