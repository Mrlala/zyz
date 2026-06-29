"""成就相关请求/响应模型

对应 SDD 4.5.8 成就接口。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AchievementItem(BaseModel):
    """成就项。"""

    id: str = ""
    name: str = ""
    description: str = ""
    icon: str | None = None
    exp_reward: int = 0
    category: str = ""


class UnlockedAchievement(BaseModel):
    """已解锁成就项。"""

    id: str = ""
    name: str = ""
    icon: str | None = None
    exp_reward: int = 0
    unlocked_at: datetime | None = None


class InProgressAchievement(BaseModel):
    """进行中成就项。"""

    id: str = ""
    name: str = ""
    icon: str | None = None
    current: int = 0
    target: int = 0


class MyAchievementsResponse(BaseModel):
    """我的成就响应数据。"""

    unlocked: list[dict[str, Any]] = Field(default_factory=list)
    in_progress: list[dict[str, Any]] = Field(default_factory=list)


class AchievementRankingItem(BaseModel):
    """成就排行榜项。"""

    rank: int = 0
    user_id: int = 0
    nickname: str = ""
    achievement_count: int = 0
    exp: int = 0
