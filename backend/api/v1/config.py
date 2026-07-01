"""配置查询接口

提供前端可读取的服务配置状态，如 AI 大模型是否已配置可用。
对应 D16：DeepSeek Key 配置检测。
"""
from __future__ import annotations

from fastapi import APIRouter

from config import settings
from schemas import BaseResponse

router = APIRouter(prefix="/config", tags=["配置"])


@router.get("/ai-status", response_model=BaseResponse)
async def get_ai_status() -> BaseResponse:
    """检测 AI 服务配置状态。

    公开接口（无需鉴权），返回 AI 大模型是否已配置可用，
    便于前端在设置页展示服务状态、在翻译失败时给出更准确的提示。
    """
    has_key = bool(settings.DEEPSEEK_API_KEY)
    return BaseResponse(data={
        "available": has_key,
        "model": settings.DEEPSEEK_MODEL,
        "mode": "AI实时翻译" if has_key else "本地词库模式",
    })
