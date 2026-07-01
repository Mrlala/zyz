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
    _run_migrations()


def _run_migrations() -> None:
    """轻量级数据库迁移：为已有表补充新增列（SQLite ALTER TABLE ADD COLUMN）。

    create_all 只创建新表，不修改已有表结构。新增字段需手动加列。
    """
    from sqlalchemy import inspect, text

    migrations = [
        # (表名, 列名, 列定义)
        ("correction_reports", "reviewer_id", "INTEGER"),
        ("correction_reports", "reviewed_at", "DATETIME"),
        ("correction_reports", "review_comment", "TEXT"),
        ("words", "created_by_admin_id", "INTEGER"),
    ]
    inspector = inspect(engine)
    for table_name, column_name, column_def in migrations:
        try:
            existing_columns = [c["name"] for c in inspector.get_columns(table_name)]
        except Exception:
            continue  # 表不存在则跳过
        if column_name not in existing_columns:
            try:
                with engine.connect() as conn:
                    conn.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
                    )
                    conn.commit()
            except Exception:
                pass  # 忽略重复执行或权限错误
