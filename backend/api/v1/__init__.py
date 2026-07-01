"""API v1 版本路由

汇总注册各业务模块路由，对外暴露统一的 api_router。
对应 SDD 4.5 接口设计中的全部 33 个接口。
"""
from fastapi import APIRouter

from api.v1.translate import router as translate_router
from api.v1.word import router as word_router
from api.v1.category import router as category_router
from api.v1.user import router as user_router
from api.v1.hot import router as hot_router
from api.v1.achievement import router as achievement_router
from api.v1.feedback import router as feedback_router
from api.v1.correction import router as correction_router
from api.v1.submission import router as submission_router
from api.v1.admin import router as admin_router
from api.v1.config import router as config_router

api_router = APIRouter()

# 翻译接口（4.5.3）
api_router.include_router(translate_router)
# 词条接口（4.5.4）
api_router.include_router(word_router)
# 分类接口（4.5.5）
api_router.include_router(category_router)
# 用户接口（4.5.6）
api_router.include_router(user_router)
# 热词接口（4.5.7）
api_router.include_router(hot_router)
# 成就接口（4.5.8）
api_router.include_router(achievement_router)
# 反馈接口（4.5.9）
api_router.include_router(feedback_router)
# 纠错接口（4.5.10）
api_router.include_router(correction_router)
# 用户提交接口（4.5.11）
api_router.include_router(submission_router)
# 后台管理接口（4.5.12）
api_router.include_router(admin_router)
# 配置查询接口（D16）
api_router.include_router(config_router)

__all__ = ["api_router"]
