"""成就与投票模型

对应 SDD 4.4.15 ~ 4.4.17：
- Achievement：成就配置表
- UserAchievement：用户成就关联表
- VoteRecord：投票记录表
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
    UniqueConstraint,
    func,
)

from models.base import Base


class Achievement(Base):
    """成就配置表，定义称号与徽章的解锁条件及奖励经验值。"""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(50), nullable=False, unique=True, comment="成就名称")
    description = Column(String(255), nullable=False, comment="成就描述")
    type = Column(String(10), nullable=False, comment="类型：title/badge")
    icon = Column(String(255), nullable=True, comment="图标 URL 或标识")
    condition = Column(JSON, nullable=False, comment='解锁条件，如 {"learn_count": 10}')
    experience_reward = Column(
        Integer, nullable=False, default=0, comment="解锁奖励经验值"
    )

    __table_args__ = (Index("idx_achievements_type", "type"),)


class UserAchievement(Base):
    """用户成就关联表，记录用户已解锁的成就。"""

    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户")
    achievement_id = Column(
        Integer, ForeignKey("achievements.id"), nullable=False, comment="成就"
    )
    unlocked_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="解锁时间",
    )

    __table_args__ = (
        Index("idx_user_achievements_user_id", "user_id"),
        Index("idx_user_achievements_achievement_id", "achievement_id"),
        UniqueConstraint(
            "user_id", "achievement_id", name="uk_user_achievements"
        ),
    )


class VoteRecord(Base):
    """投票记录表，支撑 words.vote_count 统计与防重复投票。"""

    __tablename__ = "vote_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="投票用户")
    word_id = Column(
        Integer, ForeignKey("words.id"), nullable=False, comment="被投票词条"
    )
    vote_type = Column(
        String(10), nullable=False, comment="投票类型：upvote/downvote"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="投票时间",
    )

    __table_args__ = (
        Index("idx_vote_records_user_id", "user_id"),
        Index("idx_vote_records_word_id", "word_id"),
        UniqueConstraint("user_id", "word_id", name="uk_vote_records_user_word"),
    )
