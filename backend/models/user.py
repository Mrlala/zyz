"""用户相关模型

对应 SDD 4.4.8 ~ 4.4.10：
- User：用户主表（账号 + 游戏化属性 + 偏好）
- LearnRecord：学习记录表
- Favorite：收藏表
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

from models.base import Base, BaseModel


class User(BaseModel):
    """用户主表，支持账号登录与设备登录两种方式。"""

    __tablename__ = "users"

    username = Column(String(50), nullable=False, unique=True, comment="登录用户名")
    nickname = Column(String(50), nullable=True, comment="昵称")
    password_hash = Column(String(255), nullable=True, comment="密码哈希（设备登录可空）")
    email = Column(String(100), nullable=True, unique=True, comment="邮箱")
    device_id = Column(String(255), nullable=True, unique=True, comment="设备 ID（游客/设备登录）")
    avatar = Column(String(255), nullable=True, comment="头像 URL")
    experience = Column(Integer, nullable=False, default=0, comment="经验值")
    level = Column(Integer, nullable=False, default=1, comment="用户等级")
    title = Column(String(50), nullable=True, comment="称号")
    preferences = Column(JSON, nullable=True, comment="偏好设置，如主题、关注分类")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    __table_args__ = (Index("idx_users_level", "level"),)


class LearnRecord(Base):
    """学习记录表，记录用户对词条的学习状态。"""

    __tablename__ = "learn_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="词条")
    status = Column(
        String(15),
        nullable=False,
        default="learned",
        comment="状态：learned/mastered/unmastered",
    )
    learned_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="学习时间",
    )

    __table_args__ = (
        Index("idx_learn_records_user_id", "user_id"),
        Index("idx_learn_records_word_id", "word_id"),
        UniqueConstraint("user_id", "word_id", name="uk_learn_records_user_word"),
    )


class Favorite(Base):
    """收藏表，用户收藏的词条列表。"""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="词条")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="收藏时间",
    )

    __table_args__ = (
        Index("idx_favorites_user_id", "user_id"),
        UniqueConstraint("user_id", "word_id", name="uk_favorites_user_word"),
    )
