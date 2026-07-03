"""管理员账号管理接口

- GET    /manage/accounts：账号列表（分页/筛选角色/状态）
- POST   /manage/accounts：创建管理员账号
- PUT    /manage/accounts/{id}：更新账号（昵称/角色/状态）
- DELETE /manage/accounts/{id}：删除账号（不能删自己、不能删最后一个 sys_admin）
- POST   /manage/accounts/{id}/reset-password：重置密码

权限点：system:user:manage
对应 plan-admin-system.md 第五章 5.8。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from core.security import hash_password, validate_password_strength
from models.admin import AdminAccount, Role
from schemas import BaseResponse

router = APIRouter(prefix="/accounts", tags=["管理员账号管理"])


# ---- 请求模型 ----

class AccountCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    nickname: str | None = Field(None, max_length=50)
    role_id: int = Field(..., gt=0)


class AccountUpdateRequest(BaseModel):
    nickname: str | None = Field(None, max_length=50)
    role_id: int | None = Field(None, gt=0)
    status: str | None = Field(None, description="active/disabled")


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


# ---- 接口 ----

@router.get("", response_model=BaseResponse)
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    keyword: str | None = Query(None),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:user:manage")),
) -> BaseResponse:
    """管理员账号列表。"""
    query = select(AdminAccount)
    if role_id:
        query = query.where(AdminAccount.role_id == role_id)
    if status_filter:
        query = query.where(AdminAccount.status == status_filter)
    if keyword:
        query = query.where(AdminAccount.username.like(f"%{keyword}%"))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = query.order_by(AdminAccount.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    accounts = db.execute(query).scalars().all()

    items = [
        {
            "id": a.id,
            "username": a.username,
            "nickname": a.nickname,
            "role_id": a.role_id,
            "role_code": a.role.code if a.role else None,
            "role_name": a.role.name if a.role else None,
            "status": a.status,
            "last_login_at": a.last_login_at,
            "must_change_password": a.must_change_password,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in accounts
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.post("", response_model=BaseResponse)
async def create_account(
    body: AccountCreateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:user:manage")),
) -> BaseResponse:
    """创建管理员账号。"""
    # 校验用户名唯一
    exists = db.execute(select(AdminAccount).where(AdminAccount.username == body.username)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    # 校验角色存在
    role = db.get(Role, body.role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    # 密码强度校验
    ok, msg = validate_password_strength(body.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    account = AdminAccount(
        username=body.username,
        password_hash=hash_password(body.password),
        nickname=body.nickname,
        role_id=body.role_id,
        status="active",
        must_change_password=True,
        created_by=admin.id,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return BaseResponse(data={"id": account.id, "username": account.username})


@router.put("/{account_id}", response_model=BaseResponse)
async def update_account(
    account_id: int,
    body: AccountUpdateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:user:manage")),
) -> BaseResponse:
    """更新管理员账号（昵称/角色/状态）。"""
    account = db.get(AdminAccount, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")

    if body.role_id is not None:
        role = db.get(Role, body.role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
        account.role_id = body.role_id
    if body.nickname is not None:
        account.nickname = body.nickname
    if body.status is not None:
        if body.status not in ("active", "disabled"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status 取值非法")
        # 不能禁用自己
        if body.status == "disabled" and account.id == admin.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用自己的账号")
        account.status = body.status

    db.commit()
    return BaseResponse(data={"id": account.id, "updated_at": account.updated_at.isoformat() if account.updated_at else None})


@router.delete("/{account_id}", response_model=BaseResponse)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:user:manage")),
) -> BaseResponse:
    """删除管理员账号。

    限制：不能删除自己；不能删除最后一个 sys_admin（避免无人管理系统）。
    """
    account = db.get(AdminAccount, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    if account.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己")
    # 不能删除最后一个 sys_admin
    if account.role and account.role.code == "sys_admin":
        sys_admin_count = db.execute(
            select(func.count(AdminAccount.id))
            .join(Role, AdminAccount.role_id == Role.id)
            .where(Role.code == "sys_admin", AdminAccount.status == "active")
        ).scalar_one()
        if sys_admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除最后一个系统管理员")

    db.delete(account)
    db.commit()
    return BaseResponse(data={"id": account_id, "deleted": True})


@router.post("/{account_id}/reset-password", response_model=BaseResponse)
async def reset_password(
    account_id: int,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("system:user:manage")),
) -> BaseResponse:
    """重置管理员密码（重置后强制改密）。"""
    account = db.get(AdminAccount, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    ok, msg = validate_password_strength(body.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    account.password_hash = hash_password(body.new_password)
    account.must_change_password = True
    db.commit()
    return BaseResponse(data={"id": account.id, "reset": True})
