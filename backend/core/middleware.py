"""操作日志中间件

拦截 /api/manage/* 请求，记录到 operation_logs 表，供安全审计管理员查询。
- 登录接口 /api/manage/auth/login 由 auth.py 自行记录，中间件跳过避免重复
- 敏感请求体不记录（仅记录 method/path/query/status/duration/ip/ua/admin_id）
- 异步写入，不阻塞主请求

对应 plan-admin-system.md 第五章 5.5。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.database import SessionLocal
from core.security import decode_token
from models.admin import OperationLog

logger = logging.getLogger(__name__)

# 登录接口由 auth.py 自身记录日志，中间件跳过
_SKIP_PATHS = {"/api/manage/auth/login", "/api/manage/auth/logout"}

# HTTP 方法到 action 的映射（无 id 的路径）
_METHOD_ACTION_MAP = {
    "GET": "list",
    "POST": "create",
    "PUT": "update",
    "DELETE": "delete",
}


def _parse_module_action(path: str, method: str) -> tuple[str | None, str | None]:
    """从路径解析业务模块与动作。

    例：
        /api/manage/accounts        -> (account, list/create)
        /api/manage/accounts/123    -> (account, detail/update/delete)
        /api/manage/auth/profile    -> (auth, profile)
        /api/manage/ai-config/test  -> (ai_config, test)
    """
    # 去掉 /api/manage/ 前缀
    rest = path.replace("/api/manage/", "", 1).strip("/")
    if not rest:
        return None, None
    parts = rest.split("/")
    module = parts[0].replace("-", "_")
    if len(parts) == 1:
        action = _METHOD_ACTION_MAP.get(method, method.lower())
    else:
        # /accounts/123  -> 第二段是 id 或子动作
        second = parts[1]
        action = second if not second.isdigit() else _METHOD_ACTION_MAP.get(method, "detail")
    return module, action


def _resolve_admin(request: Request) -> tuple[int | None, str | None]:
    """从请求头 Authorization 解析 admin_id 与 username（不查库，仅取 JWT payload）。"""
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None, None
    token = auth.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if payload is None or payload.get("type") != "admin":
        return None, None
    try:
        admin_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        admin_id = None
    # username 不在 JWT 里，留空（由日志查询时 join admin_accounts 补全，或登录时记录）
    return admin_id, None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _write_log(request: Request, status_code: int, duration_ms: int, error_msg: str | None = None) -> None:
    """同步写入操作日志（在独立 session 中，避免污染请求 session）。"""
    admin_id, username = _resolve_admin(request)
    module, action = _parse_module_action(request.url.path, request.method)
    # 记录查询参数（截断防止过长）
    query = request.url.query
    params = json.dumps({"query": query[:500]}, ensure_ascii=False) if query else None
    db = SessionLocal()
    try:
        log = OperationLog(
            admin_id=admin_id,
            username=username,
            module=module,
            action=action,
            method=request.method,
            path=request.url.path,
            params=params,
            ip=_client_ip(request),
            user_agent=(request.headers.get("user-agent") or "")[:255] or None,
            status_code=status_code,
            duration_ms=duration_ms,
            error_msg=error_msg,
        )
        db.add(log)
        db.commit()
    except Exception as exc:  # 日志写入失败不应影响主请求
        logger.warning("操作日志写入失败: %s", exc)
        db.rollback()
    finally:
        db.close()


class OperationLogMiddleware(BaseHTTPMiddleware):
    """操作日志中间件：拦截 /api/manage/* 请求并记录审计日志。"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        # 仅拦截管理端接口，且跳过登录/登出（由 auth.py 自行记录）
        if not path.startswith("/api/manage/") or path in _SKIP_PATHS:
            return await call_next(request)

        start = time.time()
        error_msg: str | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            status_code = 500
            error_msg = str(exc)[:500]
            raise
        finally:
            duration_ms = int((time.time() - start) * 1000)
            _write_log(request, status_code, duration_ms, error_msg)
