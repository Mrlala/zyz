"""用户提交与纠错模型

对应 SDD 4.4.12 ~ 4.4.13：
- Submission：用户提交表（新词提交）
- CorrectionReport：纠错表
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


class Submission(Base):
    """用户提交表，用户提交的新词条，经审核通过后可生成正式 words 记录。"""

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="提交者")
    word = Column(String(100), nullable=False, comment="词条名称")
    meaning = Column(Text, nullable=False, comment="释义")
    example = Column(Text, nullable=True, comment="示例")
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False, comment="建议分类"
    )
    status = Column(
        String(10),
        nullable=False,
        default="pending",
        comment="状态：pending/approved/rejected",
    )
    vote_count = Column(Integer, nullable=False, default=0, comment="投票数")
    reviewer_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="审核人"
    )
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="提交时间",
    )

    __table_args__ = (
        Index("idx_submissions_user_id", "user_id"),
        Index("idx_submissions_status", "status"),
        Index("idx_submissions_category_id", "category_id"),
        Index("idx_submissions_vote_count", "vote_count"),
    )


class CorrectionReport(Base):
    """纠错表，用户对已有词条发起的纠错报告。"""

    __tablename__ = "correction_reports"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="被纠错词条")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="提交者")
    type = Column(
        String(20),
        nullable=False,
        comment="类型：meaning_wrong/example_wrong/outdated/other",
    )
    content = Column(Text, nullable=False, comment="纠错内容说明")
    status = Column(
        String(10),
        nullable=False,
        default="pending",
        comment="状态：pending/approved/rejected",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="提交时间",
    )

    __table_args__ = (
        Index("idx_correction_reports_word_id", "word_id"),
        Index("idx_correction_reports_user_id", "user_id"),
        Index("idx_correction_reports_status", "status"),
    )
