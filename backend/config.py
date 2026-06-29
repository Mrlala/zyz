"""配置管理模块

基于 pydantic-settings 读取环境变量与 .env 文件，集中管理全局配置。
运行目录默认为 backend/，因此 .env 文件应放置在 backend/ 目录下。
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    DEEPSEEK_MODEL: str = "deepseek-chat"


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例，避免重复读取环境变量。"""
    return Settings()


# 全局配置实例，供各模块直接导入使用
settings = get_settings()
