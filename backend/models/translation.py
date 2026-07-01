"""翻译历史模型

对应 SDD 4.4.11 translations（翻译历史表）。
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)

from models.base import Base


class TranslationFavorite(Base):
    """翻译结果收藏表（D12）。"""

    __tablename__ = "translation_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户")
    translation_id = Column(
        Integer, ForeignKey("translations.id"), nullable=False, comment="翻译记录"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="收藏时间",
    )

    __table_args__ = (
        Index("idx_translation_favorites_user_id", "user_id"),
        UniqueConstraint(
            "user_id", "translation_id", name="uk_translation_favorites_user_translation"
        ),
    )


class Translation(Base):
    """翻译历史表，记录用户翻译结果，支持结果回溯与质量反馈关联。"""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="用户（游客可空）"
    )
    original_text = Column(Text, nullable=False, comment="原文")
    result = Column(JSON, nullable=False, comment="翻译结果，含释义、风险、建议等")
    mode = Column(
        String(10), nullable=False, default="translate", comment="模式：dict/translate"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )

    __table_args__ = (
        Index("idx_translations_user_id", "user_id"),
        Index("idx_translations_created_at", "created_at"),
    )
