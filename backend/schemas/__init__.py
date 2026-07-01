"""Pydantic 请求/响应模型（Schemas）

汇总导出全部 Schemas，供 API 路由层引用。
按 SDD 4.5 接口设计组织，覆盖翻译、词条、分类、用户、热词、成就、反馈、纠错与提交等模块。
"""
from schemas.base import BaseResponse
from schemas.translate import (
    DictRequest,
    DictResponse,
    DictHit,
    KeywordResult,
    RelatedItem,
    RiskInfo,
    TranslateRequest,
    TranslateResponse,
)
from schemas.word import (
    CategoryBrief,
    FavoriteRequest,
    FavoriteResponse,
    SearchResponse,
    WordDetail,
    WordItem,
    WordListResponse,
)
from schemas.category import (
    CategoryItem,
    CategoryTree,
    CategoryWordsResponse,
)
from schemas.user import (
    AccountLoginRequest,
    AccountRegisterRequest,
    AuthResponse,
    LoginRequest,
    PreferencesResponse,
    PreferencesUpdate,
    ProfileUpdateRequest,
    RegisterRequest,
    UserResponse,
)
from schemas.hot import (
    DailyHotResponse,
    HistoryResponse,
    RankingItem,
    RankingResponse,
    VoteRequest,
    VoteResponse,
)
from schemas.achievement import (
    AchievementItem,
    AchievementRankingItem,
    MyAchievementsResponse,
    UnlockedAchievement,
    InProgressAchievement,
)
from schemas.feedback import FeedbackRequest, FeedbackResponse
from schemas.correction import CorrectionRequest, CorrectionResponse
from schemas.submission import (
    SubmissionItem,
    SubmissionListResponse,
    SubmissionRequest,
    SubmissionResponse,
)

__all__ = [
    # 基础
    "BaseResponse",
    # 翻译
    "TranslateRequest",
    "DictRequest",
    "TranslateResponse",
    "KeywordResult",
    "RiskInfo",
    "RelatedItem",
    "DictHit",
    "DictResponse",
    # 词条
    "WordItem",
    "WordDetail",
    "WordListResponse",
    "SearchResponse",
    "FavoriteRequest",
    "FavoriteResponse",
    "CategoryBrief",
    # 分类
    "CategoryItem",
    "CategoryTree",
    "CategoryWordsResponse",
    # 用户
    "RegisterRequest",
    "LoginRequest",
    "AccountRegisterRequest",
    "AccountLoginRequest",
    "ProfileUpdateRequest",
    "AuthResponse",
    "UserResponse",
    "PreferencesUpdate",
    "PreferencesResponse",
    # 热词
    "DailyHotResponse",
    "VoteRequest",
    "VoteResponse",
    "RankingItem",
    "RankingResponse",
    "HistoryResponse",
    # 成就
    "AchievementItem",
    "UnlockedAchievement",
    "InProgressAchievement",
    "MyAchievementsResponse",
    "AchievementRankingItem",
    # 反馈
    "FeedbackRequest",
    "FeedbackResponse",
    # 纠错
    "CorrectionRequest",
    "CorrectionResponse",
    # 提交
    "SubmissionRequest",
    "SubmissionResponse",
    "SubmissionItem",
    "SubmissionListResponse",
]
