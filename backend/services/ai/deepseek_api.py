"""DeepSeek 官方辅助 API 封装

代理调用 DeepSeek 官方接口（余额查询、模型列表），避免向前端暴露 api_key。
文档：
- 查询余额 https://api-docs.deepseek.com/zh-cn/api/get-user-balance
- 列出模型 https://api-docs.deepseek.com/zh-cn/api/list-models
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# 官方基础 URL（不含 /v1，余额/模型接口在根路径下）
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# 辅助接口超时（秒）
AUX_TIMEOUT = 10


async def query_balance(api_key: str) -> dict[str, Any]:
    """查询 DeepSeek 账户余额。

    :param api_key: DeepSeek API Key
    :return: 官方返回结构 {is_available, balance_infos[]}
    :raises RuntimeError: 调用失败时抛出
    """
    if not api_key:
        raise RuntimeError("未配置 deepseek_api_key，无法查询余额")

    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    url = f"{DEEPSEEK_BASE_URL}/user/balance"
    try:
        async with httpx.AsyncClient(timeout=AUX_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("DeepSeek 余额查询 HTTP 错误: %s %s", exc.response.status_code, exc.response.text[:200])
        raise RuntimeError(f"余额查询失败（HTTP {exc.response.status_code}）") from exc
    except httpx.HTTPError as exc:
        logger.warning("DeepSeek 余额查询网络错误: %s", exc)
        raise RuntimeError(f"余额查询失败: {exc}") from exc


async def list_models(api_key: str) -> list[dict[str, Any]]:
    """列出 DeepSeek 当前可用模型。

    :param api_key: DeepSeek API Key
    :return: 模型列表 [{id, object, owned_by}, ...]
    :raises RuntimeError: 调用失败时抛出
    """
    if not api_key:
        raise RuntimeError("未配置 deepseek_api_key，无法查询模型列表")

    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    url = f"{DEEPSEEK_BASE_URL}/models"
    try:
        async with httpx.AsyncClient(timeout=AUX_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
    except httpx.HTTPStatusError as exc:
        logger.warning("DeepSeek 模型列表 HTTP 错误: %s %s", exc.response.status_code, exc.response.text[:200])
        raise RuntimeError(f"模型列表查询失败（HTTP {exc.response.status_code}）") from exc
    except httpx.HTTPError as exc:
        logger.warning("DeepSeek 模型列表网络错误: %s", exc)
        raise RuntimeError(f"模型列表查询失败: {exc}") from exc


# ---- 模型弃用检测与定价表 ----

# 将于 2026/07/24 弃用的旧模型名
DEPRECATED_MODELS = {"deepseek-chat", "deepseek-reasoner"}
# 弃用截止日期（北京时间）
DEPRECATION_DEADLINE = "2026-07-24 23:59"

# 模型定价表（元/百万 token，来源 https://api-docs.deepseek.com/zh-cn/quick_start/pricing）
# 字段：input_cache_hit（缓存命中）、input_cache_miss（缓存未命中）、output
MODEL_PRICING: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": {
        "input_cache_hit": 0.02,
        "input_cache_miss": 1.0,
        "output": 2.0,
    },
    "deepseek-v4-pro": {
        "input_cache_hit": 0.025,
        "input_cache_miss": 3.0,
        "output": 6.0,
    },
    # 兼容旧模型（按 deepseek-v4-flash 非思考模式计价）
    "deepseek-chat": {
        "input_cache_hit": 0.02,
        "input_cache_miss": 1.0,
        "output": 2.0,
    },
    "deepseek-reasoner": {
        "input_cache_hit": 0.025,
        "input_cache_miss": 3.0,
        "output": 6.0,
    },
}

# 默认模型（用于一键切换弃用模型）
DEFAULT_REPLACEMENT_MODEL = "deepseek-v4-flash"


def is_model_deprecated(model: str) -> bool:
    """检测模型是否即将弃用。"""
    return model in DEPRECATED_MODELS


def get_model_pricing(model: str) -> dict[str, float]:
    """获取模型定价表，未配置的模型回退到 flash 定价。"""
    return MODEL_PRICING.get(model, MODEL_PRICING["deepseek-v4-flash"])


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
) -> str:
    """按模型定价估算成本（元）。

    :param model: 模型名
    :param prompt_tokens: 输入 token 总数
    :param completion_tokens: 输出 token 数
    :param cached_tokens: 缓存命中的输入 token 数（从 usage.prompt_cache_hit_tokens 取）
    :return: 成本字符串（6 位小数）
    """
    pricing = get_model_pricing(model)
    # 输入 token 拆分：缓存命中部分 + 未命中部分
    non_cached_input = max(prompt_tokens - cached_tokens, 0)
    cost = (
        cached_tokens / 1_000_000 * pricing["input_cache_hit"]
        + non_cached_input / 1_000_000 * pricing["input_cache_miss"]
        + completion_tokens / 1_000_000 * pricing["output"]
    )
    return f"{cost:.6f}"
