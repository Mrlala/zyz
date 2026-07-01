"""用户相关请求/响应模型

对应 SDD 4.5.6 用户接口。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求。

    :param device_id: 设备唯一标识
    :param nickname: 昵称，默认「匿名用户」
    """

    device_id: str = Field(..., min_length=1, description="设备唯一标识")
    nickname: str | None = Field(None, description="昵称，默认匿名用户")


class LoginRequest(BaseModel):
    """登录请求。"""

    device_id: str = Field(..., min_length=1, description="设备唯一标识")


class AccountRegisterRequest(BaseModel):
    """账号密码注册请求。"""

    username: str = Field(..., min_length=2, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class AccountLoginRequest(BaseModel):
    """账号密码登录请求。"""

    username: str = Field(..., min_length=2, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class ProfileUpdateRequest(BaseModel):
    """用户资料更新请求（昵称、头像）。"""

    nickname: str | None = Field(None, min_length=1, max_length=20, description="昵称")
    avatar: str | None = Field(None, description="头像标识或 URL")


class AuthResponse(BaseModel):
    """登录/注册响应数据。"""

    user_id: int
    token: str
    expires_in: int = 604800


class UserResponse(BaseModel):
    """用户信息响应数据。"""

    user_id: int
    nickname: str = ""
    avatar: str | None = None
    level: int = 1
    title: str = ""
    exp: int = 0
    next_level_exp: int = 0
    favorite_count: int = 0
    submission_count: int = 0
    achievement_count: int = 0
    registered_at: datetime | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


class PreferencesUpdate(BaseModel):
    """偏好设置更新请求。

    :param default_mode: 默认翻译模式 translate/dict
    :param show_risk_advice: 是否显示风险提示
    :param font_size: 字号 small/medium/large
    :param theme: 主题 light/dark/auto
    """

    default_mode: str | None = Field(None, description="默认翻译模式 translate/dict")
    show_risk_advice: bool | None = Field(None, description="是否显示风险提示")
    font_size: str | None = Field(None, description="字号 small/medium/large")
    theme: str | None = Field(None, description="主题 light/dark/auto")


class PreferencesResponse(BaseModel):
    """偏好设置响应数据。"""

    default_mode: str = "translate"
    show_risk_advice: bool = True
    font_size: str = "medium"
    theme: str = "auto"
    updated_at: datetime | None = None
