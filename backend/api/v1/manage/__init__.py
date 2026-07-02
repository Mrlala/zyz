"""后台管理接口模块

聚合 manage 下各子模块路由，统一前缀 /manage。
对应 plan-admin-system.md 第五章 5.8 接口清单。
"""
from fastapi import APIRouter

from api.v1.manage.auth import router as auth_router
from api.v1.manage.dashboard import router as dashboard_router
from api.v1.manage.account import router as account_router
from api.v1.manage.role import router as role_router
from api.v1.manage.word_manage import router as word_manage_router
from api.v1.manage.category import router as category_router
from api.v1.manage.content_audit import router as content_audit_router
from api.v1.manage.ai_config import router as ai_config_router
from api.v1.manage.monitor import router as monitor_router
from api.v1.manage.audit import router as audit_router
from api.v1.manage.search import router as search_router

manage_router = APIRouter(prefix="/manage", tags=["后台管理"])
manage_router.include_router(auth_router)
manage_router.include_router(dashboard_router)
manage_router.include_router(account_router)
manage_router.include_router(role_router)
manage_router.include_router(word_manage_router)
manage_router.include_router(category_router)
manage_router.include_router(content_audit_router)
manage_router.include_router(ai_config_router)
manage_router.include_router(monitor_router)
manage_router.include_router(audit_router)
manage_router.include_router(search_router)

__all__ = ["manage_router"]
