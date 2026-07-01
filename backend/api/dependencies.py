"""API 路由公共依赖

提供数据库会话、JWT 用户认证与设备 ID 解析等依赖项。
对应 SDD 4.5.2 认证方案。
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_token
from models.user import User

# Bearer Token 提取器，auto_error=False 使未携带 Token 时不自动抛 401
bearer_scheme = HTTPBearer(auto_error=False)

# Token 有效期（秒），与 config.ACCESS_TOKEN_EXPIRE_MINUTES 对齐（7 天）
TOKEN_EXPIRES_IN = 604800


def _get_admin_user_ids() -> set[int]:
    """从环境变量 ADMIN_USER_IDS 读取管理员用户 ID 集合（逗号分隔）。"""
    raw = os.environ.get("ADMIN_USER_IDS", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    """从 JWT Token 解析当前用户（可选认证）。

    未携带 Token 或 Token 无效时返回 None，不抛异常。
    适用于翻译等可选认证接口。
    """
    if credentials is None or not credentials.credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        return None
    # 使用显式 SELECT 以避免 session 缓存问题
    user = db.execute(
        select(User).where(User.id == user_id_int)
    ).scalar_one_or_none()
    return user


def get_current_user_required(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """必须认证：未登录或 Token 失效时抛 401。"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或认证已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_admin_user(
    user: User = Depends(get_current_user_required),
) -> User:
    """管理员认证：已认证但非管理员时抛 403。

    管理员用户 ID 通过环境变量 ADMIN_USER_IDS 配置（逗号分隔）。
    """
    if user.id not in _get_admin_user_ids():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无管理员权限",
        )
    return user


def get_device_id(
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
) -> Optional[str]:
    """从请求头 X-Device-Id 获取设备 ID。

    用于未登录用户的设备级标识（如反馈防刷）。
    """
    return x_device_id
