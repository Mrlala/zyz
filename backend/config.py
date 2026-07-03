"""配置管理模块

基于 pydantic-settings 读取环境变量与 .env 文件，集中管理全局配置。
运行目录默认为 backend/，因此 .env 文件应放置在 backend/ 目录下。
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# 已知的弱密钥（开发默认值），生产环境禁止使用
_WEAK_SECRET_KEYS = {
    "your-secret-key-change-in-production",
    "change-me",
    "secret",
    "",
}


class Settings(BaseSettings):
    """全局配置类

    所有配置项均可通过环境变量或 .env 文件覆盖，便于在不同环境下部署。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 数据库连接
    DATABASE_URL: str = "sqlite:///./zyz.db"

    # 鉴权相关
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 默认 7 天

    # DeepSeek AI 服务
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"

    # 后台管理员用户 ID（逗号分隔，对应 users 表 id）
    ADMIN_USER_IDS: str = ""


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例，避免重复读取环境变量。"""
    return Settings()


# 全局配置实例，供各模块直接导入使用
settings = get_settings()


def is_secret_key_weak() -> bool:
    """检查 SECRET_KEY 是否为弱密钥（默认值或空）。"""
    return settings.SECRET_KEY in _WEAK_SECRET_KEYS or len(settings.SECRET_KEY) < 16


def enforce_secret_key_in_production() -> None:
    """生产环境强制校验 SECRET_KEY。

    通过 ENVIRONMENT=production 标识生产环境，
    若 SECRET_KEY 为弱密钥则拒绝启动并打印明确指引。
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in ("production", "prod"):
        if is_secret_key_weak():
            logger.warning(
                "⚠️  SECRET_KEY 使用默认弱密钥，生产环境必须通过环境变量或 .env 覆盖。"
                "请生成强密钥：python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return

    if is_secret_key_weak():
        raise RuntimeError(
            "❌ 生产环境拒绝启动：SECRET_KEY 为弱密钥或未设置。\n"
            "请在 backend/.env 文件中设置强密钥，例如：\n"
            "  SECRET_KEY=<运行 python -c \"import secrets; print(secrets.token_urlsafe(32))\" 生成>\n"
            "或通过环境变量 export SECRET_KEY=... 设置。"
        )

