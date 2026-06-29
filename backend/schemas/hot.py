"""热词相关请求/响应模型

对应 SDD 4.5.7 热词接口。
"""
from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, Field


class RankingItem(BaseModel):
    """排行榜项。"""

    rank: int = 0
    id: int = 0
    word: str = ""
    heat: float = 0.0
    vote_count: int = 0


class DailyHotResponse(BaseModel):
    """每日热词响应数据。"""

    date: str = ""
    list: List[dict[str, Any]] = Field(default_factory=list)


class RankingResponse(BaseModel):
    """热词排行榜响应数据。"""

    period: str = "daily"
    list: List[dict[str, Any]] = Field(default_factory=list)


class VoteRequest(BaseModel):
    """投票请求（无请求体，此模型用于文档占位）。"""


class VoteResponse(BaseModel):
    """投票响应数据。"""

    word_id: int
    vote_count: int
    has_voted: bool = True


class HistoryResponse(BaseModel):
    """学习历史响应数据。"""

    list: List[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
