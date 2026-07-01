"""数据模型层

汇总导出全部表的 SQLAlchemy 模型，导入本包即触发所有模型注册到 Base.metadata。
"""
from models.base import Base
from models.category import Category
from models.word import Word, WordAlias, WordContext, WordRelation
from models.user import User, LearnRecord, Favorite
from models.translation import Translation, TranslationFavorite
from models.submission import Submission, CorrectionReport
from models.feedback import Feedback
from models.achievement import Achievement, UserAchievement, VoteRecord
from models.admin import (
    AdminAccount,
    Role,
    Permission,
    RolePermission,
    OperationLog,
    AiCallLog,
    SystemConfig,
)

__all__ = [
    "Base",
    # 分类
    "Category",
    # 词条
    "Word",
    "WordAlias",
    "WordContext",
    "WordRelation",
    # 用户
    "User",
    "LearnRecord",
    "Favorite",
    # 翻译
    "Translation",
    "TranslationFavorite",
    # 提交与纠错
    "Submission",
    "CorrectionReport",
    # 反馈
    "Feedback",
    # 成就与投票
    "Achievement",
    "UserAchievement",
    "VoteRecord",
    # 后台管理
    "AdminAccount",
    "Role",
    "Permission",
    "RolePermission",
    "OperationLog",
    "AiCallLog",
    "SystemConfig",
]
