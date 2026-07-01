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
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("monitor:api:view")),
) -> BaseResponse:
    """API 调用统计：总数、成功率、平均耗时、按模块分组、近7天每日趋势。"""
    total = db.execute(select(func.count(OperationLog.id))).scalar_one()
    success_count = db.execute(
        select(func.count(OperationLog.id)).where(OperationLog.status_code < 400)
    ).scalar_one()
    error_count = total - success_count
    avg_duration = db.execute(
        select(func.avg(OperationLog.duration_ms))
    ).scalar_one() or 0
    success_rate = (success_count / total) if total else 0.0

    # 按模块分组统计
    module_rows = db.execute(
        select(
            OperationLog.module,
            func.count(OperationLog.id).label("count"),
            func.avg(OperationLog.duration_ms).label("avg_duration"),
        )
        .where(OperationLog.module.is_not(None))
        .group_by(OperationLog.module)
        .order_by(func.count(OperationLog.id).desc())
    ).all()
    by_module = [
        {
            "module": row.module,
            "count": row.count,
            "avg_duration_ms": round(float(row.avg_duration or 0), 2),
        }
        for row in module_rows
    ]

    # 近 7 天每日趋势（按 UTC 日期分组）
    start, _ = _recent_days_range(7)
    daily_rows = db.execute(
        select(
            func.date(OperationLog.created_at).label("date"),
            func.count(OperationLog.id).label("count"),
        )
        .where(OperationLog.created_at >= start)
        .group_by(func.date(OperationLog.created_at))
        .order_by(func.date(OperationLog.created_at))
    ).all()
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
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("monitor:ai:view")),
) -> BaseResponse:
    """AI 调用统计：总调用数、成功率、总 token、总成本、近7天趋势。"""
    total = db.execute(select(func.count(AiCallLog.id))).scalar_one()
    success_count = db.execute(
        select(func.count(AiCallLog.id)).where(AiCallLog.success.is_(True))
    ).scalar_one()
    fallback_count = db.execute(
        select(func.count(AiCallLog.id)).where(AiCallLog.fallback_used.is_(True))
    ).scalar_one()
    total_tokens = db.execute(
        select(func.coalesce(func.sum(AiCallLog.total_tokens), 0))
    ).scalar_one() or 0

    # cost_estimate 是字符串，需逐条转 float 求和（SQLite 无 CAST AS FLOAT 通用做法用 Python 求和）
    cost_rows = db.execute(
        select(AiCallLog.cost_estimate).where(AiCallLog.cost_estimate.is_not(None))
    ).scalars().all()
    total_cost = 0.0
    for c in cost_rows:
        try:
            total_cost += float(c)
        except (TypeError, ValueError):
            continue

    success_rate = (success_count / total) if total else 0.0

    # 近 7 天每日趋势
    start, _ = _recent_days_range(7)
    daily_rows = db.execute(
        select(
            func.date(AiCallLog.created_at).label("date"),
            func.count(AiCallLog.id).label("count"),
        )
        .where(AiCallLog.created_at >= start)
        .group_by(func.date(AiCallLog.created_at))
        .order_by(func.date(AiCallLog.created_at))
    ).all()
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
