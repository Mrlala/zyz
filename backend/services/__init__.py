"""服务层

按模块组织业务逻辑，服务层不直接处理 HTTP 请求，仅通过传入的 db session 操作数据库。
子模块：
- translator：翻译引擎与关键词匹配
- ai：AI 客户端、Prompt 模板与降级策略
- hotword_service：热词推荐与排行
- achievement_service：经验值、等级与成就
- feedback_service：质量反馈与纠错联动
- word_service：词条全生命周期管理
- user_service：用户注册登录与偏好
"""
from services.translator.engine import TranslationEngine
from services.translator.matcher import KeywordMatcher
from services.ai.client import AIClient
from services.ai.fallback import FallbackHandler
from services.hotword_service import HotWordService
from services.achievement_service import AchievementService
from services.feedback_service import FeedbackService
from services.word_service import WordService
from services.user_service import UserService

__all__ = [
    "TranslationEngine",
    "KeywordMatcher",
    "AIClient",
    "FallbackHandler",
    "HotWordService",
    "AchievementService",
    "FeedbackService",
    "WordService",
    "UserService",
]
