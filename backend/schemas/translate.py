"""翻译相关请求/响应模型

对应 SDD 4.5.3 翻译接口。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """翻译请求。

    :param text: 待翻译原文，长度 1-500
    :param mode: 翻译模式：translate（默认，中译中）/ dict（词典匹配）
    """

    text: str = Field(..., min_length=1, max_length=500, description="待翻译原文")
    mode: str = Field("translate", description="翻译模式：translate/dict")


class DictRequest(BaseModel):
    """词典匹配请求（仅 text 字段）。"""

    text: str = Field(..., min_length=1, max_length=500, description="待匹配原文")


class KeywordResult(BaseModel):
    """关键词命中项。"""

    word: str = ""
    meaning: str = ""
    source: str = "database"
    confidence: Any = "medium"
    category: str | None = None


class RiskInfo(BaseModel):
    """风险评估结果。"""

    risk_level: str = "low"
    risk_types: list[str] = Field(default_factory=list)
    advice: str = ""


class RelatedItem(BaseModel):
    """相关词条项。"""

    id: int | None = None
    word: str = ""
    similarity: float | None = None


class TranslateResponse(BaseModel):
    """翻译结果响应数据。

    字段与 TranslationEngine.translate 返回结构对齐。
    """

    translation: str = ""
    keywords: list[dict[str, Any]] = Field(default_factory=list)
    context: str = ""
    subtext: str = ""
    suggestion: str = ""
    suggested_reply: str = ""
    risk: dict[str, Any] = Field(default_factory=dict)
    related: list[dict[str, Any]] = Field(default_factory=list)
    fallback: bool = False
    feedback_enabled: bool = True


class DictHit(BaseModel):
    """词典匹配命中项。"""

    id: int
    word: str
    pinyin: str | None = None
    definition: str = ""
    tags: list[str] = Field(default_factory=list)
    match_score: float = 1.0


class DictResponse(BaseModel):
    """词典匹配响应数据。"""

    hits: list[DictHit] = Field(default_factory=list)
    total: int = 0
