"""成就接口

对应 SDD 4.5.8：
- GET /achievements：成就列表
- GET /achievements/mine：我的成就
- GET /achievements/ranking：成就排行榜
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_required
from core.database import get_db
from models.achievement import Achievement, UserAchievement
from models.user import User
from schemas import BaseResponse
from services.achievement_service import AchievementService

router = APIRouter(prefix="/achievements", tags=["成就"])


@router.get("", response_model=BaseResponse)
async def list_achievements(
    db: Session = Depends(get_db),
) -> BaseResponse:
    """获取全部成就列表。"""
    achievements = (
        db.execute(select(Achievement).order_by(Achievement.id))
        .scalars()
        .all()
    )

    items = [
        {
            "id": f"A{a.id:03d}",
            "name": a.name,
            "description": a.description,
            "icon": a.icon,
            "exp_reward": a.experience_reward,
            "category": a.type,
        }
        for a in achievements
    ]
    return BaseResponse(data=items)


@router.get("/mine", response_model=BaseResponse)
async def my_achievements(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """获取我的成就（已解锁 + 进行中）。"""
    # 已解锁成就
    unlocked_rows = (
        db.execute(
            select(UserAchievement, Achievement)
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)
            .where(UserAchievement.user_id == user.id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        .all()
    )
    unlocked = [
        {
            "id": f"A{ach.id:03d}",
            "name": ach.name,
            "icon": ach.icon,
            "exp_reward": ach.experience_reward,
            "unlocked_at": ua.unlocked_at.isoformat() if ua.unlocked_at else None,
        }
        for ua, ach in unlocked_rows
    ]

    # 进行中：未解锁的成就
    unlocked_ids = {ach.id for _, ach in unlocked_rows}
    all_achievements = db.execute(select(Achievement)).scalars().all()
    in_progress = [
        {
            "id": f"A{a.id:03d}",
            "name": a.name,
            "icon": a.icon,
            "current": 0,
            "target": _extract_target(a.condition),
        }
        for a in all_achievements
        if a.id not in unlocked_ids
    ]

    return BaseResponse(data={
        "unlocked": unlocked,
        "in_progress": in_progress,
    })


@router.get("/ranking", response_model=BaseResponse)
async def achievement_ranking(
    limit: int = Query(50, ge=1, le=100, description="返回条数"),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """获取成就排行榜。"""
    service = AchievementService()
    rankings = service.get_ranking(db, limit=limit)

    items = [
        {
            "rank": idx + 1,
            "user_id": r.get("user_id"),
            "nickname": r.get("nickname") or r.get("username"),
            "achievement_count": r.get("badge_count", 0) + r.get("title_count", 0),
            "exp": r.get("experience", 0),
        }
        for idx, r in enumerate(rankings)
    ]
    return BaseResponse(data=items)


def _extract_target(condition: dict | None) -> int:
    """从成就条件 JSON 中提取目标值。"""
    if not condition:
        return 0
    for value in condition.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
    return 0
