"""AI 客户端

封装 DeepSeek 大模型 API 调用，含鉴权、超时与重试控制。
对应 SDD 5.2 AI 服务模块。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from config import settings
from services.ai.prompts import BUILD_TRANSLATE_PROMPT

logger = logging.getLogger(__name__)

# 超时时间（秒）
REQUEST_TIMEOUT = 30
# 失败重试次数
MAX_RETRIES = 1

# DeepSeek 定价（元/千 token，deepseek-chat）
PRICE_INPUT_PER_1K = 0.001
PRICE_OUTPUT_PER_1K = 0.002


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> str:
    """估算调用成本（元）。"""
    cost = prompt_tokens / 1000 * PRICE_INPUT_PER_1K + completion_tokens / 1000 * PRICE_OUTPUT_PER_1K
    return f"{cost:.6f}"


class AIClient:
    """DeepSeek 大模型调用客户端。

    从 config 读取 DEEPSEEK_API_KEY 与 DEEPSEEK_API_URL，使用 httpx.AsyncClient 异步调用。
    每次调用记录 AiCallLog（token 消耗/耗时/成本）。
    """

    def __init__(self) -> None:
        self.api_key: str = settings.DEEPSEEK_API_KEY
        self.api_url: str = settings.DEEPSEEK_API_URL
        self.model: str = settings.DEEPSEEK_MODEL
        # 调用上下文（供日志记录关联用，可空）
        self.call_user_id: int | None = None
        self.call_admin_id: int | None = None
        self.call_endpoint: str = "translate"
        self.call_mode: str | None = None

    def _record_call_log(
        self,
        success: bool,
        duration_ms: int,
        usage: dict[str, Any] | None = None,
        error_msg: str | None = None,
        fallback_used: bool = False,
    ) -> None:
        """记录 AI 调用日志到 ai_call_logs 表（失败不影响主流程）。"""
        try:
            from core.database import SessionLocal
            from models.admin import AiCallLog

            usage = usage or {}
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
            db = SessionLocal()
            try:
                log = AiCallLog(
                    admin_id=self.call_admin_id,
                    user_id=self.call_user_id,
                    endpoint=self.call_endpoint,
                    mode=self.call_mode,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    duration_ms=duration_ms,
                    success=success,
                    fallback_used=fallback_used,
                    error_msg=error_msg,
                    cost_estimate=_estimate_cost(prompt_tokens, completion_tokens) if success else None,
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception as exc:  # 日志写入失败不影响主流程
            logger.warning("AiCallLog 写入失败: %s", exc)

    async def chat(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """调用 DeepSeek Chat 接口并解析返回的 JSON 结果。

        :param system_prompt: 系统提示词
        :param user_prompt: 用户提示词
        :return: 解析后的 JSON 字典
        :raises RuntimeError: 调用失败或 JSON 解析失败时抛出
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "stream": False,
        }

        start = time.time()
        last_error: Exception | None = None
        # 含首次调用共 MAX_RETRIES + 1 次
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    resp = await client.post(self.api_url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    duration_ms = int((time.time() - start) * 1000)
                    self._record_call_log(success=True, duration_ms=duration_ms, usage=usage)
                    return self._parse_content(content)
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                logger.warning("AI 调用失败（第 %d 次）: %s", attempt + 1, exc)
            except (KeyError, IndexError) as exc:
                last_error = exc
                logger.warning("AI 返回结构异常: %s", exc)

        duration_ms = int((time.time() - start) * 1000)
        self._record_call_log(
            success=False, duration_ms=duration_ms,
            error_msg=str(last_error)[:500] if last_error else "unknown",
        )
        raise RuntimeError(f"AI 服务调用失败: {last_error}")

    async def translate(
        self, text: str, matched_words: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """翻译入口：构建 Prompt 并调用大模型，返回结构化结果。

        :param text: 待翻译原文
        :param matched_words: 关键词匹配器命中的词库词条列表
        :return: AI 结构化结果字典
        """
        system_prompt, user_prompt = BUILD_TRANSLATE_PROMPT(text, matched_words)
        return await self.chat(system_prompt, user_prompt)

    @staticmethod
    def _parse_content(content: str) -> dict[str, Any]:
        """解析模型返回的文本内容为 JSON 字典。

        兼容模型可能附加的 markdown 代码块包裹。
        """
        text = content.strip()
        # 去除可能的 markdown 代码块包裹
        if text.startswith("```"):
            # 移除首行 ``` 或 ```json
            lines = text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return json.loads(text)
