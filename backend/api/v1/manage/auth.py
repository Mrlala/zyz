"""管理员认证接口

- POST /manage/auth/login：账号密码登录，返回管理端 JWT
- GET /manage/auth/profile：当前管理员信息 + 权限码列表
- PUT /manage/auth/password：修改自己的密码
- POST /manage/auth/logout：登出（前端清 token，记录日志）

管理端 JWT payload 含 type="admin"，与 C 端 type="user" 区分。
对应 plan-admin-system.md 第五章 5.3。
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.login_lock import (
    compute_lock_until,
    is_locked,
    lock_message,
    should_lock,
)
from core.rbac import get_admin_permissions, get_admin_required
from core.security import create_access_token, hash_password, validate_password_strength, verify_password
from models.admin import AdminAccount, OperationLog
from schemas import BaseResponse

router = APIRouter(prefix="/auth", tags=["管理员认证"])


# ---- 请求模型 ----

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128, description="至少 8 位")


# ---- 工具 ----

def _client_ip(request: Request) -> str:
    """获取客户端真实 IP（兼容反向代理）。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _record_login_log(
    db: Session,
    admin: AdminAccount | None,
    username: str,
    success: bool,
    ip: str,
    user_agent: str,
    error_msg: str | None = None,
) -> None:
    """记录登录日志到 operation_logs。"""
    log = OperationLog(
        admin_id=admin.id if admin else None,
        username=username,
        module="auth",
        action="login",
        method="POST",
        path="/api/manage/auth/login",
        params=None,
        ip=ip,
        user_agent=user_agent[:255] if user_agent else None,
        status_code=200 if success else 401,
        duration_ms=0,
        error_msg=error_msg,
    )
    db.add(log)
    db.commit()


# ---- 接口 ----

@router.post("/login", response_model=BaseResponse)
async def admin_login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> BaseResponse:
    """管理员登录。"""
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    admin = db.execute(
        select(AdminAccount).where(AdminAccount.username == body.username)
    ).scalar_one_or_none()

    # 账号锁定检查
    if admin is not None and is_locked(admin.locked_until):
        msg = lock_message(admin.locked_until)
        _record_login_log(db, admin, body.username, False, ip, user_agent, msg)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=msg,
        )

    if admin is None or not verify_password(body.password, admin.password_hash):
        # 记录失败次数（仅对已存在的账号）
        if admin is not None:
            admin.failed_login_count = (admin.failed_login_count or 0) + 1
            if should_lock(admin.failed_login_count):
                admin.locked_until = compute_lock_until()
                db.commit()
                msg = lock_message(admin.locked_until)
                _record_login_log(db, admin, body.username, False, ip, user_agent, msg)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=msg,
                )
            db.commit()
        _record_login_log(db, None, body.username, False, ip, user_agent, "用户名或密码错误")
        remaining_attempts = 5 - (admin.failed_login_count if admin else 0)
        detail = "用户名或密码错误"
        if admin is not None and remaining_attempts > 0:
            detail = f"用户名或密码错误，剩余 {remaining_attempts} 次尝试机会"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    if admin.status != "active":
        _record_login_log(db, admin, body.username, False, ip, user_agent, "账号已禁用")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已禁用，请联系系统管理员",
        )

    # 登录成功：清空失败计数和锁定
    admin.failed_login_count = 0
    admin.locked_until = None

    # 生成管理端 JWT：payload 含 type=admin + role_code + username（供中间件记录操作日志）
    token = create_access_token(
        subject=admin.id,
        extra_data={
            "type": "admin",
            "role_code": admin.role.code if admin.role else None,
            "username": admin.username,
        },
    )

    # 更新登录信息
    admin.last_login_at = datetime.now(timezone.utc).isoformat()
    admin.last_login_ip = ip
    db.commit()

    _record_login_log(db, admin, body.username, True, ip, user_agent)

    return BaseResponse(data={
        "token": token,
        "admin_id": admin.id,
        "username": admin.username,
        "nickname": admin.nickname or admin.username,
        "role_code": admin.role.code if admin.role else None,
        "role_name": admin.role.name if admin.role else None,
        "must_change_password": admin.must_change_password,
    })


@router.get("/profile", response_model=BaseResponse)
async def admin_profile(
    admin: AdminAccount = Depends(get_admin_required),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """当前管理员信息 + 权限码列表。"""
    permission_codes = sorted(get_admin_permissions(db, admin))
    return BaseResponse(data={
        "admin_id": admin.id,
        "username": admin.username,
        "nickname": admin.nickname or admin.username,
        "role_id": admin.role_id,
        "role_code": admin.role.code if admin.role else None,
        "role_name": admin.role.name if admin.role else None,
        "permissions": permission_codes,
        "last_login_at": admin.last_login_at,
        "must_change_password": admin.must_change_password,
    })


@router.put("/password", response_model=BaseResponse)
async def change_password(
    body: ChangePasswordRequest,
    admin: AdminAccount = Depends(get_admin_required),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """修改自己的密码。"""
    if not verify_password(body.old_password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )
    if body.old_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与原密码相同",
        )
    # 统一密码强度校验
    ok, msg = validate_password_strength(body.new_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    admin.password_hash = hash_password(body.new_password)
    admin.must_change_password = False
    db.commit()
    return BaseResponse(data={"updated_at": datetime.now(timezone.utc).isoformat()})


@router.post("/logout", response_model=BaseResponse)
async def admin_logout(
    admin: AdminAccount = Depends(get_admin_required),
) -> BaseResponse:
    """登出。

    前端清 token 即可；服务端不维护黑名单（短期 token + 7 天过期）。
    """
    return BaseResponse(data={"message": "已登出"})
