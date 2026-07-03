"""安全模块

提供：
- 密码哈希与校验（passlib bcrypt）
- JWT Token 生成与解析（python-jose）
- 密码强度校验（统一策略：至少 8 位 + 数字 + 字母）
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

# bcrypt 哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码最小长度
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """校验密码强度（统一策略）。

    :param password: 明文密码
    :return: (是否通过, 错误信息)；通过时错误信息为空字符串
    """
    if not password:
        return False, "密码不能为空"
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"密码至少 {PASSWORD_MIN_LENGTH} 位"
    if len(password) > PASSWORD_MAX_LENGTH:
        return False, f"密码不能超过 {PASSWORD_MAX_LENGTH} 位"
    if not (any(c.isdigit() for c in password) and any(c.isalpha() for c in password)):
        return False, "密码需至少包含数字和字母"
    return True, ""


def create_access_token(
    subject: str | int,
    extra_data: Optional[dict[str, Any]] = None,
) -> str:
    """生成 JWT 访问令牌。

    :param subject: 令牌主体，通常为用户 ID
    :param extra_data: 额外载荷数据
    :return: 编码后的 JWT 字符串
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {"exp": expire, "sub": str(subject)}
    if extra_data:
        payload.update(extra_data)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """解析并校验 JWT 令牌，失败返回 None。"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
