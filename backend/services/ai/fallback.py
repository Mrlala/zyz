"""降级策略

AI 服务超时或失败时，回退为纯词库模式，仅返回词库匹配结果。
对应 SDD 5.2 失败降级流程。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 关键词匹配项类型
KeywordMatch = dict[str, Any]


class FallbackHandler:
    """AI 失败降级处理器。"""

    def handle(
        self,
        text: str,
        matched_words: list[KeywordMatch],
        error: Exception | None = None,
    ) -> dict[str, Any]:
        """AI 不可用时组装降级结果。

        :param text: 原文
        :param matched_words: 词库匹配结果
        :param error: 触发降级的异常
        :return: 降级结果字典，fallback=true
        """
        reason = self._classify_error(error)
        logger.warning("触发降级，原因=%s，原文=%s", reason, text[:50])

        # 拼接词库命中释义作为基础翻译
        if matched_words:
            meaning_parts = [
                f"{w.get('word', '')}：{w.get('meaning', '')}" for w in matched_words
            ]
            base_translation = "；".join(meaning_parts)
        else:
            base_translation = ""

        translation = "（AI服务暂不可用，以下为词库匹配结果）" + base_translation

        return {
            "translation": translation,
            "keywords": matched_words,
            "context": "未知",
            "subtext": "AI 服务暂不可用，仅展示词库结果",
            "suggestion": "",
            "suggested_reply": "",
            "risk": {"risk_level": "low", "risk_types": [], "advice": ""},
            "related": [],
            "fallback": True,
            "fallback_reason": reason,
        }

    @staticmethod
    def _classify_error(error: Exception | None) -> str:
        """根据异常类型归类降级原因。"""
        if error is None:
            return "service_unavailable"
        name = type(error).__name__.lower()
        msg = str(error).lower()
        if "timeout" in name or "timeout" in msg:
            return "ai_timeout"
        if "json" in msg or "decode" in msg or "parse" in msg:
            return "parse_error"
        return "service_unavailable"
