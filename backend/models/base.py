"""基础模型模块

定义：
- Base：SQLAlchemy 声明式基类
- BaseModel：含 id / created_at / updated_at 公共字段的抽象模型
- CreatedAtMixin：仅含 created_at 的混入，供无更新时间的表使用
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.orm import declarative_base

# SQLAlchemy 声明式基类，所有模型均继承自 Base
Base = declarative_base()


class BaseModel(Base):
    """基础模型抽象类

    提供公共字段：id（主键）、created_at（创建时间）、updated_at（更新时间）。
    需要全部三个公共字段的表继承本类；仅需 created_at 的表可使用 CreatedAtMixin。
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间",
    )


class CreatedAtMixin:
    """仅含创建时间的混入，供无更新时间字段的表使用。"""

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
