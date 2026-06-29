"""用户提交相关请求/响应模型

对应 SDD 4.5.11 用户提交接口。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List

from pydantic import BaseModel, Field


class SubmissionRequest(BaseModel):
    """提交新词条请求。

    :param word: 词条名，1-20 字
    :param pinyin: 拼音
    :param definition: 释义，最长 200 字
    :param category_id: 分类 ID
    :param tags: 标签列表
    :param example: 例句
    """

    word: str = Field(..., min_length=1, max_length=20, description="词条名")
    pinyin: str | None = Field(None, description="拼音")
    definition: str = Field(..., min_length=1, max_length=200, description="释义")
    category_id: int | None = Field(None, description="分类 ID")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    example: str | None = Field(None, description="例句")


class SubmissionResponse(BaseModel):
    """提交响应数据。"""

    submission_id: int
    status: str = "pending"
    submitted_at: datetime | None = None


class SubmissionItem(BaseModel):
    """提交列表项。"""

    submission_id: int
    word: str = ""
    status: str = "pending"
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None


class SubmissionListResponse(BaseModel):
    """提交列表响应数据。"""

    list: List[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
