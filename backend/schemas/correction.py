"""纠错相关请求/响应模型

对应 SDD 4.5.10 纠错接口。
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CorrectionRequest(BaseModel):
    """纠错请求。

    :param word_id: 词条 ID
    :param type: 纠错类型 meaning_wrong/example_wrong/pinyin_wrong/category_wrong/risk_wrong/outdated/other
    :param content: 纠错内容描述，最长 1000 字
    """

    word_id: int = Field(..., description="词条 ID")
    type: str = Field(
        ...,
        description="纠错类型：meaning_wrong/example_wrong/pinyin_wrong/category_wrong/risk_wrong/outdated/other"
    )
    content: str = Field(..., min_length=1, max_length=1000, description="纠错内容描述")


class CorrectionResponse(BaseModel):
    """纠错响应数据。"""

    correction_id: int
    status: str = "pending"
    submitted_at: datetime | None = None
