"""数据库连接与 Session 管理

基于 SQLAlchemy 2.0 提供：
- 全局引擎 engine
- 会话工厂 SessionLocal
- FastAPI 依赖 get_db
- 建表函数 init_db
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

# SQLite 需要 check_same_thread=False 以支持多线程访问（FastAPI 线程池）
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供数据库会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """创建所有数据表。

    需先导入 models 包以触发模型注册，再调用 metadata.create_all。
    幂等操作：已存在的表不会被重复创建。
    """
    # 导入模型包以注册所有表到 Base.metadata
    import models  # noqa: F401
    from models.base import Base

    Base.metadata.create_all(bind=engine)
