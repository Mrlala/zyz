"""用户接口

对应 SDD 4.5.6：
- POST /user/register：用户注册（设备 ID）
- POST /user/login：用户登录（设备 ID）
- GET /user/profile：用户信息
- PUT /user/preferences：更新偏好设置
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_required, TOKEN_EXPIRES_IN
from core.database import get_db
from core.security import create_access_token
from models.submission import Submission
from models.translation import Translation, TranslationFavorite
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


@router.get("/favorites", response_model=BaseResponse)
async def list_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """获取当前用户收藏的词条列表（分页）。"""
    from models.word import Word
    from models.category import Category

    # 基础查询：当前用户的收藏 + 关联词条
    base = (
        select(Favorite, Word)
        .join(Word, Favorite.word_id == Word.id)
        .where(
            Favorite.user_id == user.id,
            Word.status == "published",
            Word.deleted_at.is_(None),
        )
    )
    total = db.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()

    # 分页 + 按收藏时间倒序
    rows = db.execute(
        base.order_by(Favorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # 批量查询分类
    category_ids = {w.id: w.category_id for _, w in rows if w.category_id}
    categories = {}
    if category_ids:
        cats = db.execute(
            select(Category).where(Category.id.in_(set(category_ids.values())))
        ).scalars().all()
        categories = {c.id: c for c in cats}

    items = []
    for fav, w in rows:
        cat = categories.get(w.category_id) if w.category_id else None
        items.append({
            "id": w.id,
            "word": w.word,
            "pinyin": w.pinyin,
            "summary": w.summary,
            "category_id": w.category_id,
            "category_name": cat.name if cat else "",
            "favorite_count": 0,
            "is_favorited": True,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None,
        })

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/translations/{translation_id}/favorite", response_model=BaseResponse)
async def toggle_translation_favorite(
    translation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """收藏/取消收藏翻译结果（D12，toggle 切换）。"""
    translation = db.get(Translation, translation_id)
    if translation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="翻译记录不存在")

    existing = db.execute(
        select(TranslationFavorite).where(
            TranslationFavorite.user_id == user.id,
            TranslationFavorite.translation_id == translation_id,
        )
    ).scalars().first()

    if existing:
        db.delete(existing)
        db.commit()
        return BaseResponse(data={"is_favorited": False, "message": "已取消收藏"})

    fav = TranslationFavorite(user_id=user.id, translation_id=translation_id)
    db.add(fav)
    db.commit()
    return BaseResponse(data={"is_favorited": True, "message": "已收藏"})


@router.get("/translation-favorites", response_model=BaseResponse)
async def list_translation_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """获取当前用户收藏的翻译结果列表（D12，分页）。"""
    base = (
        select(TranslationFavorite, Translation)
        .join(Translation, TranslationFavorite.translation_id == Translation.id)
        .where(TranslationFavorite.user_id == user.id)
    )
    total = db.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()

    rows = db.execute(
        base.order_by(TranslationFavorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        {
            "id": t.id,
            "original_text": t.original_text,
            "result": t.result,
            "mode": t.mode,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None,
        }
        for fav, t in rows
    ]

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
