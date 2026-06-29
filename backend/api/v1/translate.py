"""翻译接口

对应 SDD 4.5.3：
- POST /translate：中译中翻译（调用 TranslationEngine）
- POST /translate/dict：词典模式匹配
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_device_id
from core.database import get_db
from models.translation import Translation
from models.user import User
from schemas import BaseResponse, DictRequest, TranslateRequest
from services.translator.engine import TranslationEngine

router = APIRouter(prefix="/translate", tags=["翻译"])


@router.post("", response_model=BaseResponse)
async def translate(
    request: TranslateRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    device_id: str | None = Depends(get_device_id),
) -> BaseResponse:
    """中译中翻译。

    调用 TranslationEngine 完成词库匹配 + AI 生成，返回结构化翻译结果。
    认证可选：已认证用户可触发反馈开关并记录翻译历史。
    """
    if request.mode not in ("translate", "dict"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mode 取值非法，仅支持 translate/dict",
        )

    engine = TranslationEngine()
    result = await engine.translate(request.text, request.mode, db)

    # 记录翻译历史，便于反馈关联
    translation_record = Translation(
        user_id=user.id if user else None,
        original_text=request.text,
        result=result,
        mode=request.mode,
    )
    db.add(translation_record)
    db.commit()
    db.refresh(translation_record)

    # 已认证用户允许反馈
    result["feedback_enabled"] = user is not None
    result["translation_id"] = translation_record.id
    return BaseResponse(data=result)


@router.post("/dict", response_model=BaseResponse)
async def translate_dict(
    request: DictRequest,
    db: Session = Depends(get_db),
) -> BaseResponse:
    """词典模式匹配。

    直接对输入文本执行词库匹配，返回命中词条列表。
    """
    engine = TranslationEngine()
    matches = engine.match_keywords(request.text, db)

    hits = [
        {
            "id": m.get("word_id"),
            "word": m.get("word", ""),
            "pinyin": None,
            "definition": m.get("meaning", ""),
            "tags": [],
            "match_score": 1.0 if m.get("source") == "database" else 0.8,
        }
        for m in matches
    ]

    if not hits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未命中任何词条",
        )

    return BaseResponse(data={"hits": hits, "total": len(hits)})
