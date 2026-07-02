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
from services.ai.deepseek_api import estimate_cost as _estimate_cost_by_model
from services.ai.prompts import BUILD_TRANSLATE_PROMPT

logger = logging.getLogger(__name__)

# 超时时间（秒）
REQUEST_TIMEOUT = 30
# 失败重试次数
MAX_RETRIES = 1

# 余额不足的 HTTP 状态码（DeepSeek 官方用 402 Payment Required）
INSUFFICIENT_BALANCE_STATUS = 402


class InsufficientBalanceError(RuntimeError):
    """DeepSeek 账户余额不足，需触发降级到词库模式。"""


class AIClient:
    """DeepSeek 大模型调用客户端。

    优先从 system_configs 表读取最新 AI 配置（后台可在线修改），回退到 .env。
    使用 httpx.AsyncClient 异步调用，每次调用记录 AiCallLog（token 消耗/耗时/成本）。
    """

    def __init__(self) -> None:
        # 调用上下文（供日志记录关联用，可空）
        self.call_user_id: int | None = None
        self.call_admin_id: int | None = None
        self.call_endpoint: str = "translate"
        self.call_mode: str | None = None
        # 配置延迟加载，每次 chat 前刷新
        self.api_key: str = ""
        self.api_url: str = ""
        self.model: str = ""
        self.temperature: float = 0.3
        self.max_tokens: int | None = None

    def _load_config(self) -> None:
        """从 system_configs 表读取最新 AI 配置（每次调用前执行）。

        优先取数据库配置，回退到 .env 环境变量。
        """
        cfg_map: dict[str, str] = {}
        try:
            from core.database import SessionLocal
            from models.admin import SystemConfig
            from sqlalchemy import select

            db = SessionLocal()
            try:
                configs = db.execute(
                    select(SystemConfig).where(SystemConfig.category == "ai")
                ).scalars().all()
                cfg_map = {c.config_key: (c.config_value or "") for c in configs}
            finally:
                db.close()
        except Exception as exc:
            logger.warning("读取 system_configs AI 配置失败，回退到 .env: %s", exc)

        self.api_key = cfg_map.get("deepseek_api_key") or settings.DEEPSEEK_API_KEY
        self.api_url = cfg_map.get("deepseek_api_url") or settings.DEEPSEEK_API_URL
        self.model = cfg_map.get("deepseek_model") or settings.DEEPSEEK_MODEL
        try:
            self.temperature = float(cfg_map.get("deepseek_temperature", "0.3") or "0.3")
        except (TypeError, ValueError):
            self.temperature = 0.3
        max_tokens_str = cfg_map.get("deepseek_max_tokens", "")
        try:
            self.max_tokens = int(max_tokens_str) if max_tokens_str else None
        except (TypeError, ValueError):
            self.max_tokens = None

    def _record_call_log(
        self,
        success: bool,
        duration_ms: int,
        usage: dict[str, Any] | None = None,
        error_msg: str | None = None,
        fallback_used: bool = False,
        model: str | None = None,
    ) -> None:
        """记录 AI 调用日志到 ai_call_logs 表（失败不影响主流程）。

        使用动态定价表按实际使用的 model 估算成本，区分缓存命中/未命中 token。
        """
        try:
            from core.database import SessionLocal
            from models.admin import AiCallLog

            usage = usage or {}
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
            # DeepSeek 返回的缓存命中 token 数（字段名 prompt_cache_hit_tokens）
            cached_tokens = int(usage.get("prompt_cache_hit_tokens", 0))
            cost_model = model or self.model
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
                    cost_estimate=(
                        _estimate_cost_by_model(
                            cost_model, prompt_tokens, completion_tokens, cached_tokens
                        )
                        if success
                        else None
                    ),
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception as exc:  # 日志写入失败不影响主流程
            logger.warning("AiCallLog 写入失败: %s", exc)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        model_override: str | None = None,
    ) -> dict[str, Any]:
        """调用 DeepSeek Chat 接口并解析返回的 JSON 结果。

        :param system_prompt: 系统提示词
        :param user_prompt: 用户提示词
        :param model_override: 场景化模型覆盖（如风险复审用 deepseek-v4-pro），
                               为 None 时使用当前配置的默认 model
        :return: 解析后的 JSON 字典
        :raises RuntimeError: 调用失败或 JSON 解析失败时抛出
        :raises InsufficientBalanceError: 余额不足（HTTP 402）时抛出，由上层触发降级
        """
        # 每次调用前从数据库刷新配置，确保后台修改即时生效
        self._load_config()
        # 场景化模型路由：覆盖默认 model
        use_model = model_override or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "stream": False,
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens

        start = time.time()
        last_error: Exception | None = None
        # 含首次调用共 MAX_RETRIES + 1 次
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    resp = await client.post(self.api_url, headers=headers, json=payload)
                    # 余额不足（402）不重试，直接抛 InsufficientBalanceError 由上层降级
                    if resp.status_code == INSUFFICIENT_BALANCE_STATUS:
                        duration_ms = int((time.time() - start) * 1000)
                        err_msg = self._extract_balance_error(resp)
                        self._record_call_log(
                            success=False,
                            duration_ms=duration_ms,
                            error_msg=err_msg,
                            fallback_used=True,
                            model=use_model,
                        )
                        raise InsufficientBalanceError(err_msg)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    duration_ms = int((time.time() - start) * 1000)
                    self._record_call_log(
                        success=True, duration_ms=duration_ms, usage=usage, model=use_model
                    )
                    return self._parse_content(content)
            except InsufficientBalanceError:
                # 余额不足直接向上抛，由翻译引擎触发降级
                raise
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
            model=use_model,
        )
        raise RuntimeError(f"AI 服务调用失败: {last_error}")

    @staticmethod
    def _extract_balance_error(resp: httpx.Response) -> str:
        """从 402 响应中提取错误信息。"""
        try:
            data = resp.json()
            err = data.get("error", {})
            msg = err.get("message") if isinstance(err, dict) else str(err)
            return f"余额不足（402）: {msg or 'Insufficient Balance'}"
        except Exception:
            return f"余额不足（402）: {resp.text[:200]}"

    async def translate(
        self, text: str, matched_words: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """翻译入口：构建 Prompt 并调用大模型，返回结构化结果。

        翻译场景默认使用当前配置的 model（推荐 deepseek-v4-flash，低成本高并发）。

        :param text: 待翻译原文
        :param matched_words: 关键词匹配器命中的词库词条列表
        :return: AI 结构化结果字典
        """
        system_prompt, user_prompt = BUILD_TRANSLATE_PROMPT(text, matched_words)
        # 翻译场景用默认 model（flash），不传 model_override
        return await self.chat(system_prompt, user_prompt)

    async def risk_review(
        self, text: str, matched_words: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """风险复审入口：用 deepseek-v4-pro 模型做高精度风险判定。

        场景化模型路由：风险复审对精度要求高，强制使用 pro 模型。
        若账户未配置 pro 模型或余额不足，自动回退到默认 model。

        :param text: 待复审原文
        :param matched_words: 关键词匹配器命中的词库词条列表
        :return: AI 结构化结果字典（含 risk 字段）
        """
        system_prompt, user_prompt = BUILD_TRANSLATE_PROMPT(text, matched_words)
        try:
            # 风险复审强制用 pro 模型（高精度）
            return await self.chat(system_prompt, user_prompt, model_override="deepseek-v4-pro")
        except Exception as exc:
            logger.warning("风险复审 pro 模型调用失败，回退默认模型: %s", exc)
            # pro 模型不可用时回退到默认 model
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
