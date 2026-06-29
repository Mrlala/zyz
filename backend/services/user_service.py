"""用户服务

用户注册、登录、资料查询、偏好管理与设备登录。
对应 SDD 5.4 用户模块。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password, verify_password
from models.achievement import UserAchievement
from models.user import Favorite, LearnRecord, User
from models.translation import Translation


class UserService:
    """用户认证与资料管理服务。"""

    def register(self, username: str, password: str, db: Session) -> User:
        """注册新用户。

        :param username: 用户名
        :param password: 明文密码
        :param db: 数据库会话
        :return: 新建用户对象
        :raises ValueError: 用户名已存在
        """
        existing = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError("用户名已存在")

        user = User(
            username=username,
            password_hash=hash_password(password),
            experience=0,
            level=1,
            title="黑话小白",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def login(self, username: str, password: str, db: Session) -> dict[str, Any]:
        """账号密码登录，签发 JWT 令牌。

        :return: {token, user} 字典
        :raises ValueError: 用户名或密码错误
        """
        user = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if user is None or not user.password_hash:
            raise ValueError("用户名或密码错误")
        if not verify_password(password, user.password_hash):
            raise ValueError("用户名或密码错误")

        user.last_login_at = datetime.now(timezone.utc)
        db.commit()

        token = create_access_token(user.id, extra_data={"username": user.username})
        return {"token": token, "user": self._to_profile(user, db)}

    def get_profile(self, user_id: int, db: Session) -> dict[str, Any]:
        """获取用户资料，含学习统计与成就计数。

        :raises ValueError: 用户不存在
        """
        user = db.get(User, user_id)
        if user is None:
            raise ValueError("用户不存在")
        return self._to_profile(user, db)

    def update_preferences(
        self, user_id: int, preferences: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """更新用户偏好设置（合并到现有 preferences JSON）。

        :return: 更新后的完整 preferences
        :raises ValueError: 用户不存在
        """
        user = db.get(User, user_id)
        if user is None:
            raise ValueError("用户不存在")

        current = user.preferences or {}
        current.update(preferences)
        user.preferences = current
        db.commit()
        return user.preferences

    def get_or_create_by_device(
        self, device_id: str, db: Session
    ) -> dict[str, Any]:
        """设备 ID 自动登录，首次自动注册。

        :param device_id: 设备唯一标识
        :param db: 数据库会话
        :return: {token, user, is_new} 字典
        :raises ValueError: 设备 ID 为空
        """
        if not device_id:
            raise ValueError("设备 ID 不能为空")

        user = db.execute(
            select(User).where(User.device_id == device_id)
        ).scalar_one_or_none()
        is_new = False
        if user is None:
            # 自动注册新用户，username 以设备 ID 派生保证唯一
            username = f"device_{device_id[:20]}"
            user = User(
                username=username,
                device_id=device_id,
                experience=0,
                level=1,
                title="黑话小白",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new = True

        user.last_login_at = datetime.now(timezone.utc)
        db.commit()

        token = create_access_token(user.id, extra_data={"username": user.username})
        return {"token": token, "user": self._to_profile(user, db), "is_new": is_new}

    def _to_profile(self, user: User, db: Session) -> dict[str, Any]:
        """组装用户资料与统计信息。"""
        learn_count = db.execute(
            select(func.count(LearnRecord.id)).where(LearnRecord.user_id == user.id)
        ).scalar_one()
        mastered_count = db.execute(
            select(func.count(LearnRecord.id)).where(
                LearnRecord.user_id == user.id, LearnRecord.status == "mastered"
            )
        ).scalar_one()
        favorite_count = db.execute(
            select(func.count(Favorite.id)).where(Favorite.user_id == user.id)
        ).scalar_one()
        translate_count = db.execute(
            select(func.count(Translation.id)).where(Translation.user_id == user.id)
        ).scalar_one()
        achievement_count = db.execute(
            select(func.count(UserAchievement.id)).where(
                UserAchievement.user_id == user.id
            )
        ).scalar_one()

        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "email": user.email,
            "experience": user.experience,
            "level": user.level,
            "title": user.title,
            "preferences": user.preferences,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "stats": {
                "learn_count": learn_count,
                "mastered_count": mastered_count,
                "favorite_count": favorite_count,
                "translate_count": translate_count,
                "achievement_count": achievement_count,
            },
        }
