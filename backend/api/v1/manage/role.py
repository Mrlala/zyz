"""角色权限管理接口

- GET /manage/roles：角色列表（含权限码）
- GET /manage/permissions：全部权限点（按 module 分组）
- PUT /manage/roles/{id}/permissions：配置角色权限

权限点：system:role:manage
对应 plan-admin-system.md 第五章 5.8。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount, Permission, Role, RolePermission
from schemas import BaseResponse

router = APIRouter(prefix="/roles", tags=["角色权限管理"])


class RolePermissionUpdateRequest(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)


@router.get("", response_model=BaseResponse)
async def list_roles(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:role:manage")),
) -> BaseResponse:
    """角色列表（含每个角色的权限码）。"""
    roles = db.execute(select(Role).order_by(Role.id)).scalars().all()
    result = []
    for r in roles:
        perm_codes = db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == r.id)
        ).scalars().all()
        result.append({
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "is_builtin": r.is_builtin,
            "permissions": sorted(perm_codes),
        })
    return BaseResponse(data={"list": result})


@router.get("/permissions/all", response_model=BaseResponse)
async def list_permissions(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:role:manage")),
) -> BaseResponse:
    """全部权限点（按 module 分组）。"""
    perms = db.execute(select(Permission).order_by(Permission.module, Permission.code)).scalars().all()
    grouped: dict[str, list[dict]] = {}
    for p in perms:
        grouped.setdefault(p.module, []).append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "module": p.module,
        })
    return BaseResponse(data={"groups": grouped})


@router.put("/{role_id}/permissions", response_model=BaseResponse)
async def update_role_permissions(
    role_id: int,
    body: RolePermissionUpdateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:role:manage")),
) -> BaseResponse:
    """配置角色的权限（全量覆盖）。"""
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 校验权限 id 合法
    valid_ids = set(
        db.execute(
            select(Permission.id).where(Permission.id.in_(body.permission_ids))
        ).scalars().all()
    )

    # 删除旧关联
    db.execute(
        RolePermission.__table__.delete().where(RolePermission.role_id == role_id)
    )
    # 建立新关联
    for pid in body.permission_ids:
        if pid in valid_ids:
            db.add(RolePermission(role_id=role_id, permission_id=pid))
    db.commit()

    return BaseResponse(data={
        "role_id": role_id,
        "permission_ids": sorted(valid_ids),
        "updated_by": admin.username,
    })
