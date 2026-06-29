"""质量反馈模型

对应 SDD 4.4.14 feedback（质量反馈表）。
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)

from models.base import Base


class Feedback(Base):
    """质量反馈表，用户对翻译结果的质量反馈。"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    translation_id = Column(
        Integer, ForeignKey("translations.id"), nullable=False, comment="关联翻译记录"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="用户（游客可空）"
    )
    device_id = Column(String(255), nullable=True, comment="设备 ID，用于防刷")
    type = Column(
        String(15),
        nullable=False,
        comment="类型：accurate/inaccurate/outdated",
    )
    comment = Column(Text, nullable=True, comment="补充说明")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="提交时间",
    )

    __table_args__ = (
        Index("idx_feedback_translation_id", "translation_id"),
        Index("idx_feedback_user_id", "user_id"),
        Index("idx_feedback_type", "type"),
    )
