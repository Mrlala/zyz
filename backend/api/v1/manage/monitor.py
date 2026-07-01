"""监控接口（后台）

- GET /monitor/api-stats：API 调用统计（聚合 operation_logs）
- GET /monitor/ai-stats：AI 调用统计（聚合 ai_call_logs）
- GET /monitor/ai-logs：AI 调用明细列表（分页）

权限点：monitor:api:view、monitor:ai:view
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount, AiCallLog, OperationLog
from schemas import BaseResponse

router = APIRouter(prefix="/monitor", tags=["监控"])


def _recent_days_range(days: int = 7) -> tuple[datetime, datetime]:
    """返回近 N 天的 UTC 时间范围 [start, now]。"""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days - 1)
    return start, now


# ---- API 调用统计 ----

@router.get("/api-stats", response_model=BaseResponse)
async def api_stats(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("monitor:api:view")),
) -> BaseResponse:
    """API 调用统计：总数、成功率、平均耗时、按模块分组、每日趋势。

    传 start_date/end_date 时按日期范围过滤所有统计；不传时保持默认行为
    （总量/模块统计为全量，趋势为近 7 天）。
    """
    date_filters = []
    if start_date:
        date_filters.append(func.date(OperationLog.created_at) >= start_date)
    if end_date:
        date_filters.append(func.date(OperationLog.created_at) <= end_date)
    has_date_filter = bool(date_filters)

    total_query = select(func.count(OperationLog.id))
    if has_date_filter:
        total_query = total_query.where(*date_filters)
    total = db.execute(total_query).scalar_one()

    success_query = select(func.count(OperationLog.id)).where(OperationLog.status_code < 400)
    if has_date_filter:
        success_query = success_query.where(*date_filters)
    success_count = db.execute(success_query).scalar_one()

    error_count = total - success_count

    avg_query = select(func.avg(OperationLog.duration_ms))
    if has_date_filter:
        avg_query = avg_query.where(*date_filters)
    avg_duration = db.execute(avg_query).scalar_one() or 0
    success_rate = (success_count / total) if total else 0.0

    # 按模块分组统计
    module_query = (
        select(
            OperationLog.module,
            func.count(OperationLog.id).label("count"),
            func.avg(OperationLog.duration_ms).label("avg_duration"),
        )
        .where(OperationLog.module.is_not(None))
        .group_by(OperationLog.module)
        .order_by(func.count(OperationLog.id).desc())
    )
    if has_date_filter:
        module_query = module_query.where(*date_filters)
    module_rows = db.execute(module_query).all()
    by_module = [
        {
            "module": row.module,
            "count": row.count,
            "avg_duration_ms": round(float(row.avg_duration or 0), 2),
        }
        for row in module_rows
    ]

    # 每日趋势：传了日期范围则按范围过滤，否则默认近 7 天
    daily_query = select(
        func.date(OperationLog.created_at).label("date"),
        func.count(OperationLog.id).label("count"),
    )
    if has_date_filter:
        daily_query = daily_query.where(*date_filters)
    else:
        start, _ = _recent_days_range(7)
        daily_query = daily_query.where(OperationLog.created_at >= start)
    daily_query = daily_query.group_by(func.date(OperationLog.created_at)).order_by(
        func.date(OperationLog.created_at)
    )
    daily_rows = db.execute(daily_query).all()
    daily_trend = [{"date": str(row.date), "count": row.count} for row in daily_rows]

    return BaseResponse(data={
        "total": total,
        "success_count": success_count,
        "error_count": error_count,
        "success_rate": round(success_rate, 4),
        "avg_duration_ms": round(float(avg_duration or 0), 2),
        "by_module": by_module,
        "daily_trend": daily_trend,
    })


# ---- AI 调用统计 ----

@router.get("/ai-stats", response_model=BaseResponse)
async def ai_stats(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("monitor:ai:view")),
) -> BaseResponse:
    """AI 调用统计：总调用数、成功率、总 token、总成本、每日趋势。

    传 start_date/end_date 时按日期范围过滤所有统计；不传时保持默认行为
    （总量统计为全量，趋势为近 7 天）。
    """
    date_filters = []
    if start_date:
        date_filters.append(func.date(AiCallLog.created_at) >= start_date)
    if end_date:
        date_filters.append(func.date(AiCallLog.created_at) <= end_date)
    has_date_filter = bool(date_filters)

    total_query = select(func.count(AiCallLog.id))
    if has_date_filter:
        total_query = total_query.where(*date_filters)
    total = db.execute(total_query).scalar_one()

    success_query = select(func.count(AiCallLog.id)).where(AiCallLog.success.is_(True))
    if has_date_filter:
        success_query = success_query.where(*date_filters)
    success_count = db.execute(success_query).scalar_one()

    fallback_query = select(func.count(AiCallLog.id)).where(AiCallLog.fallback_used.is_(True))
    if has_date_filter:
        fallback_query = fallback_query.where(*date_filters)
    fallback_count = db.execute(fallback_query).scalar_one()

    tokens_query = select(func.coalesce(func.sum(AiCallLog.total_tokens), 0))
    if has_date_filter:
        tokens_query = tokens_query.where(*date_filters)
    total_tokens = db.execute(tokens_query).scalar_one() or 0

    # cost_estimate 是字符串，需逐条转 float 求和（SQLite 无 CAST AS FLOAT 通用做法用 Python 求和）
    cost_query = select(AiCallLog.cost_estimate).where(AiCallLog.cost_estimate.is_not(None))
    if has_date_filter:
        cost_query = cost_query.where(*date_filters)
    cost_rows = db.execute(cost_query).scalars().all()
    total_cost = 0.0
    for c in cost_rows:
        try:
            total_cost += float(c)
        except (TypeError, ValueError):
            continue

    success_rate = (success_count / total) if total else 0.0

    # 每日趋势：传了日期范围则按范围过滤，否则默认近 7 天
    daily_query = select(
        func.date(AiCallLog.created_at).label("date"),
        func.count(AiCallLog.id).label("count"),
    )
    if has_date_filter:
        daily_query = daily_query.where(*date_filters)
    else:
        start, _ = _recent_days_range(7)
        daily_query = daily_query.where(AiCallLog.created_at >= start)
    daily_query = daily_query.group_by(func.date(AiCallLog.created_at)).order_by(
        func.date(AiCallLog.created_at)
    )
    daily_rows = db.execute(daily_query).all()
    daily_trend = [{"date": str(row.date), "count": row.count} for row in daily_rows]

    return BaseResponse(data={
        "total": total,
        "success_count": success_count,
        "fallback_count": fallback_count,
        "success_rate": round(success_rate, 4),
        "total_tokens": int(total_tokens),
        "total_cost": round(total_cost, 6),
        "daily_trend": daily_trend,
    })


# ---- AI 调用明细列表 ----

@router.get("/ai-logs", response_model=BaseResponse)
async def list_ai_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("monitor:ai:view")),
) -> BaseResponse:
    """AI 调用明细列表。"""
    query = select(AiCallLog)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = (
        query.order_by(AiCallLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = db.execute(query).scalars().all()

    items = [
        {
            "id": log.id,
            "admin_id": log.admin_id,
            "user_id": log.user_id,
            "endpoint": log.endpoint,
            "mode": log.mode,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "duration_ms": log.duration_ms,
            "success": log.success,
            "fallback_used": log.fallback_used,
            "error_msg": log.error_msg,
            "cost_estimate": log.cost_estimate,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})
