"""AI 配置接口（后台）

- GET  /ai-config：获取 AI 配置列表（敏感字段脱敏）
- PUT  /ai-config：批量更新 AI 配置
- POST /ai-config/test：测试 AI 连接
- GET  /ai-config/balance：查询 DeepSeek 账户余额
- GET  /ai-config/models：列出 DeepSeek 可用模型
- GET  /ai-config/deprecation：获取当前模型弃用状态
- POST /ai-config/migrate-model：一键切换弃用模型到推荐模型

权限点：ai:config:manage
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount, SystemConfig
from schemas import BaseResponse
from services.ai.deepseek_api import (
    DEPRECATION_DEADLINE,
    DEFAULT_REPLACEMENT_MODEL,
    is_model_deprecated,
    list_models,
    query_balance,
)

router = APIRouter(prefix="/ai-config", tags=["AI配置"])


# ---- 请求模型 ----

class ConfigItem(BaseModel):
    """单项配置更新。"""

    key: str = Field(..., description="配置键，如 deepseek_api_key")
    value: str = Field(..., description="配置值")


# 非敏感配置白名单：即使数据库里 is_sensitive=True 也强制明文返回
# （api_url/model 等不含密钥，显示为 *** 会影响用户编辑）
NON_SENSITIVE_KEYS = {"deepseek_api_url", "deepseek_model", "deepseek_temperature", "deepseek_max_tokens"}


# ---- 接口 ----

@router.get("", response_model=BaseResponse)
async def list_ai_config(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """获取 AI 配置列表。

    敏感字段（is_sensitive=True 且不在 NON_SENSITIVE_KEYS 白名单中）的 config_value
    显示为 "已设置" 或 "未设置"，不返回真实值。
    """
    configs = db.execute(
        select(SystemConfig).where(SystemConfig.category == "ai").order_by(SystemConfig.config_key)
    ).scalars().all()

    items = []
    for c in configs:
        # api_url 等非密钥配置强制按非敏感处理（修正历史数据 is_sensitive=True 的问题）
        effective_sensitive = c.is_sensitive and c.config_key not in NON_SENSITIVE_KEYS
        item = {
            "id": c.id,
            "key": c.config_key,
            "value_type": c.value_type,
            "category": c.category,
            "description": c.description,
            "is_sensitive": effective_sensitive,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        if effective_sensitive:
            item["value"] = "已设置" if c.config_value else "未设置"
        else:
            item["value"] = c.config_value
        items.append(item)
    return BaseResponse(data={"list": items, "total": len(items)})


@router.put("", response_model=BaseResponse)
async def update_ai_config(
    body: list[ConfigItem],
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """批量更新 AI 配置。

    请求体为 ConfigItem 数组：[{"key": "...", "value": "..."}, ...]
    """
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="配置项不能为空")

    # 取出所有 key 一次性查询，避免逐条 hit DB
    keys = [item.key for item in body]
    existing = db.execute(select(SystemConfig).where(SystemConfig.config_key.in_(keys))).scalars().all()
    existing_map = {c.config_key: c for c in existing}

    not_found_keys = [k for k in keys if k not in existing_map]
    if not_found_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项不存在: {','.join(not_found_keys)}",
        )

    updated_keys: list[str] = []
    now = datetime.now(timezone.utc)
    for item in body:
        cfg = existing_map[item.key]
        # 跳过空值（避免误清空敏感配置）
        if item.value == "":
            continue
        cfg.config_value = item.value
        cfg.updated_at = now
        updated_keys.append(item.key)

    db.commit()

    return BaseResponse(data={
        "updated_keys": updated_keys,
        "updated_count": len(updated_keys),
        "updated_at": now.isoformat(),
    })


@router.post("/test", response_model=BaseResponse)
async def test_ai_connection(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """测试 AI 连接。

    读取 SystemConfig 中的 deepseek_api_key/api_url/model，发送一条简单 prompt 验证连通性。
    数据库无配置时回退到 .env 环境变量。
    """
    from config import settings

    # 读取关键配置
    keys_needed = ["deepseek_api_key", "deepseek_api_url", "deepseek_model"]
    configs = db.execute(
        select(SystemConfig).where(SystemConfig.config_key.in_(keys_needed))
    ).scalars().all()
    config_map = {c.config_key: c.config_value for c in configs}

    # 数据库优先，回退 .env
    api_key = config_map.get("deepseek_api_key") or settings.DEEPSEEK_API_KEY or ""
    api_url = config_map.get("deepseek_api_url") or settings.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
    model = config_map.get("deepseek_model") or settings.DEEPSEEK_MODEL or "deepseek-chat"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未配置 deepseek_api_key（数据库和 .env 均无值），无法测试连接",
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个测试助手"},
            {"role": "user", "content": "你好"},
        ],
        "temperature": 0.3,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(api_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
    except httpx.TimeoutException:
        return BaseResponse(
            code=1,
            message="AI 连接测试失败：请求超时",
            data={"error": "请求超时", "api_url": api_url, "model": model},
        )
    except httpx.HTTPError as exc:
        return BaseResponse(
            code=1,
            message="AI 连接测试失败：HTTP 错误",
            data={"error": f"HTTP 错误: {exc}", "api_url": api_url, "model": model},
        )
    except (KeyError, IndexError) as exc:
        return BaseResponse(
            code=1,
            message="AI 连接测试失败：响应结构异常",
            data={"error": f"响应结构异常: {exc}", "api_url": api_url, "model": model},
        )

    return BaseResponse(data={
        "api_url": api_url,
        "model": model,
        "reply": reply,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    })


# ---- DeepSeek 辅助接口 ----

def _get_current_api_key(db: Session) -> str:
    """读取当前配置的 deepseek_api_key（数据库优先，回退 .env）。"""
    from config import settings

    cfg = db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "deepseek_api_key")
    ).scalar_one_or_none()
    return (cfg.config_value if cfg else None) or settings.DEEPSEEK_API_KEY


def _get_current_model(db: Session) -> str:
    """读取当前配置的 deepseek_model（数据库优先，回退 .env）。"""
    from config import settings

    cfg = db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "deepseek_model")
    ).scalar_one_or_none()
    return (cfg.config_value if cfg else None) or settings.DEEPSEEK_MODEL


@router.get("/balance", response_model=BaseResponse)
async def get_balance(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """查询 DeepSeek 账户余额（代理调用官方 /user/balance）。"""
    api_key = _get_current_api_key(db)
    try:
        balance = await query_balance(api_key)
        return BaseResponse(data=balance)
    except RuntimeError as exc:
        return BaseResponse(code=1, message=str(exc), data=None)


@router.get("/models", response_model=BaseResponse)
async def list_available_models(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """列出 DeepSeek 当前可用模型（代理调用官方 /models）。"""
    api_key = _get_current_api_key(db)
    try:
        models = await list_models(api_key)
        return BaseResponse(data={"list": models, "total": len(models)})
    except RuntimeError as exc:
        return BaseResponse(code=1, message=str(exc), data=None)


@router.get("/deprecation", response_model=BaseResponse)
async def get_deprecation_status(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """获取当前模型的弃用状态与推荐替换模型。"""
    current_model = _get_current_model(db)
    return BaseResponse(data={
        "current_model": current_model,
        "is_deprecated": is_model_deprecated(current_model),
        "deadline": DEPRECATION_DEADLINE,
        "recommended_model": DEFAULT_REPLACEMENT_MODEL,
    })


class MigrateModelRequest(BaseModel):
    """一键切换模型请求。"""

    target_model: str = Field(..., description="目标模型名")


@router.post("/migrate-model", response_model=BaseResponse)
async def migrate_model(
    body: MigrateModelRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """一键切换弃用模型到推荐模型（更新 system_configs.deepseek_model）。"""
    if not body.target_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_model 不能为空")

    cfg = db.execute(
        select(SystemConfig).where(SystemConfig.config_key == "deepseek_model")
    ).scalar_one_or_none()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置项 deepseek_model 不存在",
        )

    old_model = cfg.config_value
    cfg.config_value = body.target_model
    cfg.updated_at = datetime.now(timezone.utc)
    db.commit()

    return BaseResponse(data={
        "old_model": old_model,
        "new_model": body.target_model,
        "updated_at": cfg.updated_at.isoformat(),
    })
