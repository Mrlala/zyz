"""AI 配置接口（后台）

- GET  /ai-config：获取 AI 配置列表（敏感字段脱敏）
- PUT  /ai-config：批量更新 AI 配置
- POST /ai-config/test：测试 AI 连接

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

router = APIRouter(prefix="/ai-config", tags=["AI配置"])


# ---- 请求模型 ----

class ConfigItem(BaseModel):
    """单项配置更新。"""

    key: str = Field(..., description="配置键，如 deepseek_api_key")
    value: str = Field(..., description="配置值")


class ConfigUpdateRequest(BaseModel):
    """批量更新配置请求。"""

    configs: list[ConfigItem] = Field(default_factory=list)


# ---- 接口 ----

@router.get("", response_model=BaseResponse)
async def list_ai_config(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """获取 AI 配置列表。

    敏感字段（is_sensitive=True）的 config_value 显示为 "已设置" 或 "未设置"，不返回真实值。
    """
    configs = db.execute(
        select(SystemConfig).where(SystemConfig.category == "ai").order_by(SystemConfig.config_key)
    ).scalars().all()

    items = []
    for c in configs:
        item = {
            "id": c.id,
            "key": c.config_key,
            "value_type": c.value_type,
            "category": c.category,
            "description": c.description,
            "is_sensitive": c.is_sensitive,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        if c.is_sensitive:
            item["value"] = "已设置" if c.config_value else "未设置"
        else:
            item["value"] = c.config_value
        items.append(item)
    return BaseResponse(data={"list": items, "total": len(items)})


@router.put("", response_model=BaseResponse)
async def update_ai_config(
    body: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("ai:config:manage")),
) -> BaseResponse:
    """批量更新 AI 配置。"""
    if not body.configs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="配置项不能为空")

    # 取出所有 key 一次性查询，避免逐条 hit DB
    keys = [item.key for item in body.configs]
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
    for item in body.configs:
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
    """
    # 读取关键配置
    keys_needed = ["deepseek_api_key", "deepseek_api_url", "deepseek_model"]
    configs = db.execute(
        select(SystemConfig).where(SystemConfig.config_key.in_(keys_needed))
    ).scalars().all()
    config_map = {c.config_key: c.config_value for c in configs}

    api_key = config_map.get("deepseek_api_key") or ""
    api_url = config_map.get("deepseek_api_url") or "https://api.deepseek.com/v1/chat/completions"
    model = config_map.get("deepseek_model") or "deepseek-chat"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未配置 deepseek_api_key，无法测试连接",
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
        return BaseResponse(code=0, data={
            "success": False,
            "error": "请求超时",
            "api_url": api_url,
            "model": model,
        })
    except httpx.HTTPError as exc:
        return BaseResponse(code=0, data={
            "success": False,
            "error": f"HTTP 错误: {exc}",
            "api_url": api_url,
            "model": model,
        })
    except (KeyError, IndexError) as exc:
        return BaseResponse(code=0, data={
            "success": False,
            "error": f"响应结构异常: {exc}",
            "api_url": api_url,
            "model": model,
        })

    return BaseResponse(data={
        "success": True,
        "api_url": api_url,
        "model": model,
        "reply": reply,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    })
