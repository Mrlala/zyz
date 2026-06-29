"""分类相关请求/响应模型

对应 SDD 4.5.5 分类接口。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CategoryItem(BaseModel):
    """分类项（含子分类）。"""

    id: int
    name: str = ""
    icon: str | None = None
    word_count: int = 0
    children: list[dict[str, Any]] = Field(default_factory=list)


class CategoryTree(BaseModel):
    """分类树响应数据。"""

    tree: list[CategoryItem] = Field(default_factory=list)


class CategoryWordsResponse(BaseModel):
    """分类下词条响应数据。"""

    category: dict[str, Any] = Field(default_factory=dict)
    list: List[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
