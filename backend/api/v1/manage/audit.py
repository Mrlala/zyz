"""操作审计接口（后台）

- GET /audit-logs/operation：操作日志列表（分页，多条件筛选）
- GET /audit-logs/login：登录日志列表（module=auth 且 action=login）
- GET /audit-logs/export：导出操作日志（全量，限制 10000 条）

权限点：audit:log:view、audit:log:export
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount, OperationLog
from schemas import BaseResponse

router = APIRouter(prefix="/audit-logs", tags=["操作审计"])


def _serialize_log(log: OperationLog) -> dict:
    """序列化操作日志为字典。"""
    return {
        "id": log.id,
        "admin_id": log.admin_id,
        "username": log.username,
        "module": log.module,
        "action": log.action,
        "method": log.method,
        "path": log.path,
        "params": log.params,
        "ip": log.ip,
        "user_agent": log.user_agent,
        "status_code": log.status_code,
        "duration_ms": log.duration_ms,
        "error_msg": log.error_msg,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _build_operation_query(
    admin_id: int | None = None,
    module: str | None = None,
    action: str | None = None,
    status_code: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """构建操作日志查询条件。"""
    query = select(OperationLog)
    if admin_id is not None:
        query = query.where(OperationLog.admin_id == admin_id)
    if module:
        query = query.where(OperationLog.module == module)
    if action:
        query = query.where(OperationLog.action == action)
    if status_code is not None:
        query = query.where(OperationLog.status_code == status_code)
    if start_date:
        query = query.where(func.date(OperationLog.created_at) >= start_date)
    if end_date:
        query = query.where(func.date(OperationLog.created_at) <= end_date)
    return query


# ---- 接口 ----

@router.get("/operation", response_model=BaseResponse)
async def list_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_id: int | None = Query(None, description="按操作者 admin_id 筛选"),
    module: str | None = Query(None, description="按模块筛选，如 account/word/ai_config"),
    action: str | None = Query(None, description="按动作筛选，如 login/create/update/delete"),
    status_code: int | None = Query(None, description="按 HTTP 状态码筛选"),
    start_date: str | None = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="截止日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("audit:log:view")),
) -> BaseResponse:
    """操作日志列表（分页，多条件筛选，按 created_at 倒序）。"""
    query = _build_operation_query(admin_id, module, action, status_code, start_date, end_date)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = (
        query.order_by(OperationLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = db.execute(query).scalars().all()

    items = [_serialize_log(log) for log in logs]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.get("/login", response_model=BaseResponse)
async def list_login_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_id: int | None = Query(None),
    start_date: str | None = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="截止日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("audit:log:view")),
) -> BaseResponse:
    """登录日志列表（OperationLog.module==auth 且 action==login）。"""
    query = select(OperationLog).where(
        OperationLog.module == "auth",
        OperationLog.action == "login",
    )
    if admin_id is not None:
        query = query.where(OperationLog.admin_id == admin_id)
    if start_date:
        query = query.where(func.date(OperationLog.created_at) >= start_date)
    if end_date:
        query = query.where(func.date(OperationLog.created_at) <= end_date)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = (
        query.order_by(OperationLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = db.execute(query).scalars().all()

    items = [_serialize_log(log) for log in logs]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.get("/export", response_model=BaseResponse)
async def export_operation_logs(
    admin_id: int | None = Query(None),
    module: str | None = Query(None),
    action: str | None = Query(None),
    status_code: int | None = Query(None),
    start_date: str | None = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="截止日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("audit:log:export")),
) -> BaseResponse:
    """导出操作日志（不分页，限制最多 10000 条，data 里直接是 list）。

    前端可基于返回的 JSON 自行转换为 CSV/Excel。
    """
    query = _build_operation_query(admin_id, module, action, status_code, start_date, end_date)
    query = query.order_by(OperationLog.created_at.desc()).limit(10000)
    logs = db.execute(query).scalars().all()

    items = [_serialize_log(log) for log in logs]
    return BaseResponse(data=items)
