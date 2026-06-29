"""AI 子模块

封装大模型调用、Prompt 模板与失败降级策略。
"""
from services.ai.client import AIClient
from services.ai.fallback import FallbackHandler
from services.ai.prompts import BUILD_TRANSLATE_PROMPT

__all__ = ["AIClient", "FallbackHandler", "BUILD_TRANSLATE_PROMPT"]
