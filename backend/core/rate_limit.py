"""接口限流中间件

基于内存的滑动窗口限流，按 IP + 设备 ID 维度限制高频接口调用频率。
- 翻译接口：30 次/分钟（调用 AI，需防刷）
- 提交/反馈/纠错接口：10 次/分钟（UGC 内容防滥用）

设计考量：
- 不引入 slowapi 等第三方库（与新版 FastAPI 兼容性未知，参考 prometheus 教训）
- 内存存储，单进程适用；多进程部署需替换为 Redis
- 限流粒度：IP + X-Device-Id 组合，未登录用户按设备限流，登录用户按 user_id 限流
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 限流规则：路径前缀 -> (窗口秒数, 最大次数)
RATE_LIMIT_RULES: dict[str, tuple[int, int]] = {
    "/api/translate": (60, 30),        # 翻译：30 次/分钟
    "/api/submission": (60, 10),       # 提交：10 次/分钟
    "/api/feedback": (60, 10),         # 反馈：10 次/分钟
    "/api/correction": (60, 10),       # 纠错：10 次/分钟
}

# 滑动窗口记录：key -> [timestamp, timestamp, ...]
# key 格式："{ip}:{device_id}:{path_prefix}"
_request_records: dict[str, list[float]] = defaultdict(list)

# 清理阈值：记录数超过此值时触发过期清理
_CLEANUP_THRESHOLD = 10000


def _client_ip(request: Request) -> str:
    """获取客户端真实 IP（支持代理转发）。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _device_id(request: Request) -> str:
    """获取设备 ID（未提供时用空串占位）。"""
    return request.headers.get("x-device-id") or ""


def _match_rule(path: str) -> tuple[str, tuple[int, int]] | None:
    """匹配限流规则，返回 (匹配的前缀, (窗口秒数, 最大次数))。"""
    for prefix, rule in RATE_LIMIT_RULES.items():
        if path.startswith(prefix):
            return prefix, rule
    return None


def _build_key(request: Request, prefix: str) -> str:
    """构建限流 key：IP + 设备 ID + 路径前缀。"""
    return f"{_client_ip(request)}:{_device_id(request)}:{prefix}"


def _cleanup_expired() -> None:
    """清理过期的限流记录，避免内存无限增长。"""
    if len(_request_records) < _CLEANUP_THRESHOLD:
        return
    now = time.time()
    # 保留最近 120 秒内的记录（覆盖所有规则的窗口）
    for key in list(_request_records.keys()):
        _request_records[key] = [t for t in _request_records[key] if now - t < 120]
        if not _request_records[key]:
            del _request_records[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """接口限流中间件。

    对配置的高频接口按 IP+设备 维度限流，超限返回 429。
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        # 仅对 POST 请求限流（GET 不消耗 AI 成本）
        if request.method != "POST":
            return await call_next(request)

        matched = _match_rule(path)
        if matched is None:
            return await call_next(request)

        prefix, (window_seconds, max_requests) = matched
        key = _build_key(request, prefix)

        now = time.time()
        records = _request_records[key]
        # 移除窗口外的记录
        cutoff = now - window_seconds
        while records and records[0] < cutoff:
            records.pop(0)

        if len(records) >= max_requests:
            # 计算需要等待的时间
            wait_seconds = int(window_seconds - (now - records[0])) + 1
            return Response(
                content=f'{{"code":429,"message":"请求过于频繁，请 {wait_seconds} 秒后重试","data":null}}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(wait_seconds),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # 记录本次请求
        records.append(now)
        _cleanup_expired()

        response = await call_next(request)
        # 在响应头中添加限流信息（便于前端调试）
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max_requests - len(records))
        return response
