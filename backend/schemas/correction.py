"""纠错相关请求/响应模型

对应 SDD 4.5.10 纠错接口。
支持两类纠错：
- 词条纠错（target_type=word，需 word_id）
- AI 翻译纠错（target_type=ai_meaning/ai_translation，需 translation_id）
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class CorrectionRequest(BaseModel):
    """纠错请求。

    :param word_id: 词条 ID（词条纠错必填，AI 翻译纠错时为空）
    :param translation_id: 翻译记录 ID（AI 翻译纠错必填）
    :param type: 纠错类型 meaning_wrong/example_wrong/pinyin_wrong/category_wrong/risk_wrong/outdated/other/ai_meaning_wrong/ai_translation_wrong
    :param content: 纠错内容描述，最长 1000 字
    :param ai_content: AI 原始内容（AI 翻译纠错时填）
    :param target_type: 纠错目标 word/ai_meaning/ai_translation
    """

    word_id: Optional[int] = Field(None, description="词条 ID（词条纠错必填）")
    translation_id: Optional[int] = Field(None, description="翻译记录 ID（AI 翻译纠错必填）")
    type: str = Field(
        ...,
        description="纠错类型：meaning_wrong/example_wrong/pinyin_wrong/category_wrong/risk_wrong/outdated/other/ai_meaning_wrong/ai_translation_wrong"
    )
    content: str = Field(..., min_length=1, max_length=1000, description="纠错内容描述")
    ai_content: Optional[str] = Field(None, description="AI 原始内容（释义或翻译）")
    target_type: str = Field("word", description="纠错目标：word/ai_meaning/ai_translation")

    @model_validator(mode="after")
    def check_target(self):
        """word_id 和 translation_id 至少填一个。"""
        if not self.word_id and not self.translation_id:
            raise ValueError("word_id 和 translation_id 至少填一个")
        return self


class CorrectionResponse(BaseModel):
    """纠错响应数据。"""

    correction_id: int
    status: str = "pending"
    submitted_at: datetime | None = None
