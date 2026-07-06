"""纠错接口

对应 SDD 4.5.10：
- POST /corrections：提交纠错

支持两类纠错：
- 词条纠错（target_type=word）：需 word_id，校验词条存在
- AI 翻译纠错（target_type=ai_meaning/ai_translation）：需 translation_id，校验翻译记录存在
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

# 词条纠错类型
WORD_CORRECTION_TYPES = (
    "meaning_wrong", "example_wrong", "pinyin_wrong",
    "category_wrong", "risk_wrong", "outdated", "other",
)
# AI 翻译纠错类型
AI_CORRECTION_TYPES = ("ai_meaning_wrong", "ai_translation_wrong")


@router.post("", response_model=BaseResponse)
async def submit_correction(
    request: CorrectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """提交纠错报告（支持词条纠错和 AI 翻译纠错）。"""
    # 根据 target_type 校验类型
    if request.target_type == "word":
        if request.type not in WORD_CORRECTION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="type 取值非法，词条纠错仅支持 meaning_wrong/example_wrong/pinyin_wrong/category_wrong/risk_wrong/outdated/other",
            )
    elif request.target_type in ("ai_meaning", "ai_translation"):
        if request.type not in AI_CORRECTION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="type 取值非法，AI 翻译纠错仅支持 ai_meaning_wrong/ai_translation_wrong",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="target_type 取值非法，仅支持 word/ai_meaning/ai_translation",
        )

    # 敏感词过滤：检查纠错内容
    if is_sensitive_filter_enabled() and request.content and contains_sensitive(request.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="纠错内容包含敏感词，请修改后重试",
        )

    import logging
    logger = logging.getLogger(__name__)

    service = WordService()
    try:
        report = service.submit_correction(
            word_id=request.word_id,
            translation_id=request.translation_id,
            type=request.type,
            content=request.content,
            ai_content=request.ai_content,
            target_type=request.target_type,
            user_id=user.id,
            db=db,
        )
    except ValueError as exc:
        msg = str(exc)
        if "不存在" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "非法" in msg:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
        if "保存纠错报告失败" in msg:
            logger.error("纠错保存失败: %s", msg)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交失败，请稍后重试")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as exc:
        logger.error("纠错接口未预期异常: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="服务器内部错误，请稍后重试")

    return BaseResponse(data={
        "correction_id": report.id,
        "status": report.status,
        "submitted_at": report.created_at.isoformat() if report.created_at else None,
    })
