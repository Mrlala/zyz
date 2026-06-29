"""词条相关请求/响应模型

对应 SDD 4.5.4 词条接口。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List

from pydantic import BaseModel, Field


class CategoryBrief(BaseModel):
    """分类简要信息。"""

    id: int
    name: str = ""


class WordItem(BaseModel):
    """词条列表项。"""

    id: int
    word: str = ""
    pinyin: str | None = None
    summary: str = ""
    category: CategoryBrief | None = None
    tags: list[str] = Field(default_factory=list)
    view_count: int = 0
    favorite_count: int = 0
    created_at: datetime | None = None


class WordContextItem(BaseModel):
    """词条多语境项。"""

    scene: str = ""
    example: str = ""


class WordRelatedItem(BaseModel):
    """相关词条项。"""

    id: int
    word: str = ""
    relation: str = ""


class WordDetail(BaseModel):
    """词条详情。"""

    id: int
    word: str = ""
    pinyin: str | None = None
    definition: str = ""
    contexts: list[dict[str, Any]] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    related: list[dict[str, Any]] = Field(default_factory=list)
    category: CategoryBrief | None = None
    tags: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    view_count: int = 0
    favorite_count: int = 0
    is_favorited: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WordListResponse(BaseModel):
    """词条列表分页响应数据。"""

    list: List[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class SearchItem(BaseModel):
    """搜索结果项。"""

    id: int
    word: str = ""
    summary: str = ""
    highlight: str = ""
    match_score: float = 0.0


class SearchResponse(BaseModel):
    """搜索响应数据。"""

    list: List[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class FavoriteRequest(BaseModel):
    """收藏请求（无请求体，此模型用于文档占位）。"""


class FavoriteResponse(BaseModel):
    """收藏操作响应数据。"""

    word_id: int
    is_favorited: bool
    favorite_count: int
