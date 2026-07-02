"""纠错接口

对应 SDD 4.5.10：
- POST /corrections：提交纠错
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_required
from core.database import get_db
from core.sensitive_filter import contains_sensitive, is_sensitive_filter_enabled
from models.user import User
from schemas import BaseResponse, CorrectionRequest
from services.word_service import WordService

router = APIRouter(prefix="/corrections", tags=["纠错"])


@router.post("", response_model=BaseResponse)
async def submit_correction(
    request: CorrectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """提交词条纠错报告。"""
    allowed_types = (
        "meaning_wrong", "example_wrong", "pinyin_wrong",
        "category_wrong", "risk_wrong", "outdated", "other",
    )
    if request.type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="type 取值非法，仅支持 meaning_wrong/example_wrong/pinyin_wrong/category_wrong/risk_wrong/outdated/other",
        )

    # 敏感词过滤：检查纠错内容
    if is_sensitive_filter_enabled() and request.content and contains_sensitive(request.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="纠错内容包含敏感词，请修改后重试",
        )

    service = WordService()
    try:
        report = service.submit_correction(
            word_id=request.word_id,
            type=request.type,
            content=request.content,
            user_id=user.id,
            db=db,
        )
    except ValueError as exc:
        msg = str(exc)
        if "不存在" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "非法" in msg:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return BaseResponse(data={
        "correction_id": report.id,
        "status": report.status,
        "submitted_at": report.created_at.isoformat() if report.created_at else None,
    })
