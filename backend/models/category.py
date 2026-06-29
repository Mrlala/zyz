"""分类模型

对应 SDD 4.4.3 categories（分类表），支持自引用三级层级结构。
"""
from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, Integer, SmallInteger, String

from models.base import BaseModel


class Category(BaseModel):
    """分类表，支持自引用三级层级（如 直播电商 > 带货话术 > 逼单话术）。"""

    __tablename__ = "categories"

    name = Column(String(50), nullable=False, comment="分类名称")
    parent_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
        comment="父分类 ID，一级分类为 NULL",
    )
    level = Column(SmallInteger, nullable=False, default=1, comment="层级：1/2/3")
    sort_order = Column(
        Integer, nullable=False, default=0, comment="排序权重，升序"
    )
    icon = Column(String(255), nullable=True, comment="分类图标 URL 或标识")

    __table_args__ = (
        Index("idx_categories_parent_id", "parent_id"),
        Index("idx_categories_level", "level"),
        Index("idx_categories_sort", "level", "sort_order"),
    )
