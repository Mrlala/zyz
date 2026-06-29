"""用户接口

对应 SDD 4.5.6：
- POST /user/register：用户注册（设备 ID）
- POST /user/login：用户登录（设备 ID）
- GET /user/profile：用户信息
- PUT /user/preferences：更新偏好设置
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_required, TOKEN_EXPIRES_IN
from core.database import get_db
from core.security import create_access_token
from models.submission import Submission
from models.user import Favorite, User
from models.achievement import UserAchievement
from schemas import BaseResponse, PreferencesUpdate, RegisterRequest, LoginRequest
from services.user_service import UserService

router = APIRouter(prefix="/user", tags=["用户"])


@router.post("/register", response_model=BaseResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> BaseResponse:
    """用户注册（基于设备 ID）。"""
    # 校验设备是否已注册
    existing = db.execute(
        select(User).where(User.device_id == request.device_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="设备已注册",
        )

    # 创建用户，username 以设备 ID 派生保证唯一
    username = f"device_{request.device_id[:20]}"
    user = User(
        username=username,
        device_id=request.device_id,
        nickname=request.nickname or "匿名用户",
        experience=0,
        level=1,
        title="黑话小白",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        user.id,
        extra_data={"device_id": request.device_id, "username": user.username},
    )
    return BaseResponse(data={
        "user_id": user.id,
        "token": token,
        "expires_in": TOKEN_EXPIRES_IN,
    })


@router.post("/login", response_model=BaseResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> BaseResponse:
    """用户登录（基于设备 ID）。"""
    user = db.execute(
        select(User).where(User.device_id == request.device_id)
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        user.id,
        extra_data={"device_id": request.device_id, "username": user.username},
    )
    return BaseResponse(data={
        "user_id": user.id,
        "token": token,
        "expires_in": TOKEN_EXPIRES_IN,
    })


@router.get("/profile", response_model=BaseResponse)
async def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """获取用户信息（含等级、经验、统计）。"""
    service = UserService()
    profile = service.get_profile(user.id, db)

    # 按需补充提交数
    submission_count = db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == user.id)
    ).scalar_one()

    return BaseResponse(data={
        "user_id": profile.get("id"),
        "nickname": profile.get("nickname") or profile.get("username"),
        "avatar": profile.get("avatar"),
        "level": profile.get("level", 1),
        "title": profile.get("title", ""),
        "exp": profile.get("experience", 0),
        "next_level_exp": _next_level_exp(profile.get("experience", 0)),
        "favorite_count": profile.get("stats", {}).get("favorite_count", 0),
        "submission_count": submission_count,
        "achievement_count": profile.get("stats", {}).get("achievement_count", 0),
        "registered_at": profile.get("last_login_at"),
        "preferences": profile.get("preferences", {}),
    })


@router.put("/preferences", response_model=BaseResponse)
async def update_preferences(
    request: PreferencesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """更新用户偏好设置。"""
    # 字段合法性校验
    if request.default_mode is not None and request.default_mode not in ("translate", "dict"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="default_mode 取值非法",
        )
    if request.font_size is not None and request.font_size not in ("small", "medium", "large"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="font_size 取值非法",
        )
    if request.theme is not None and request.theme not in ("light", "dark", "auto"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="theme 取值非法",
        )

    # 仅更新非 None 字段
    preferences = {
        k: v for k, v in request.model_dump().items() if v is not None
    }
    service = UserService()
    updated = service.update_preferences(user.id, preferences, db)

    return BaseResponse(data={
        "default_mode": updated.get("default_mode", "translate"),
        "show_risk_advice": updated.get("show_risk_advice", True),
        "font_size": updated.get("font_size", "medium"),
        "theme": updated.get("theme", "auto"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def _next_level_exp(current_exp: int) -> int:
    """根据当前经验值计算下一级所需经验阈值。

    对齐 AchievementService 中的 LEVEL_THRESHOLDS。
    """
    from services.achievement_service import LEVEL_THRESHOLDS
    for threshold in LEVEL_THRESHOLDS:
        if current_exp < threshold:
            return threshold
    return LEVEL_THRESHOLDS[-1]
