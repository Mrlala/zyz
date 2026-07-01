"""RBAC 权限模块（后台管理）

提供管理员账号的 JWT 认证与权限校验依赖：
- get_admin_required：管理员必须认证（校验 type==admin 的 JWT）
- require_permission(code)：权限校验依赖工厂
- has_permission(admin, code)：权限判断工具

管理员 JWT 与 C 端用户 JWT 区分：payload 含 type="admin"。
对应 plan-admin-system.md 第五章 5.2/5.3。
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_token
from models.admin import AdminAccount, Permission, RolePermission

# 管理端 Bearer 提取器
admin_bearer_scheme = HTTPBearer(auto_error=False)


def get_admin_required(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(admin_bearer_scheme),
) -> AdminAccount:
    """管理员必须认证依赖。

    校验 JWT 合法且 payload.type == "admin"，返回 AdminAccount。
    未携带/无效/类型不符/账号禁用均抛 401。
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或认证已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理端令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    admin_id_raw = payload.get("sub")
    try:
        admin_id = int(admin_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌主体非法",
        )
    admin = db.execute(
        select(AdminAccount).where(AdminAccount.id == admin_id)
    ).scalar_one_or_none()
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员账号不存在",
        )
    if admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已禁用",
        )
    return admin


def get_admin_permissions(db: Session, admin: AdminAccount) -> set[str]:
    """查询管理员账号拥有的权限 code 集合。"""
    rows = db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == admin.role_id)
    ).scalars().all()
    return set(rows)


def has_permission(db: Session, admin: AdminAccount, code: str) -> bool:
    """判断管理员是否拥有指定权限点。"""
    return code in get_admin_permissions(db, admin)


def require_permission(code: str):
    """权限校验依赖工厂。

    用法：
        @router.get("...", dependencies=[Depends(require_permission("system:user:manage"))])
        或
        def handler(admin: AdminAccount = Depends(require_permission("content:word:manage"))):
    """

    def dependency(
        admin: AdminAccount = Depends(get_admin_required),
        db: Session = Depends(get_db),
    ) -> AdminAccount:
        if not has_permission(db, admin, code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限: {code}",
            )
        return admin

    return dependency
