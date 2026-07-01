"""后台管理接口模块

聚合 manage 下各子模块路由，统一前缀 /manage。
对应 plan-admin-system.md 第五章 5.8 接口清单。

子模块按阶段逐步加入：
- auth：管理员登录/认证（阶段 A）
- dashboard：工作台概览（阶段 B）
- account：账号管理（阶段 B）
- role：角色权限（阶段 B）
- word_manage：词库管理（阶段 B）
- category：分类管理（阶段 B）
- content_audit：内容审核（阶段 B）
- ai_config：AI 配置（阶段 B）
- monitor：API/AI 监控（阶段 B）
- audit：操作日志（阶段 B）
"""
from fastapi import APIRouter

from api.v1.manage.auth import router as auth_router

manage_router = APIRouter(prefix="/manage", tags=["后台管理"])
manage_router.include_router(auth_router)

__all__ = ["manage_router"]
