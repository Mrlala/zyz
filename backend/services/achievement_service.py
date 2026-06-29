"""成就服务

经验值累计、等级提升、称号/徽章解锁判定与成就排行榜。
对应 SDD 5.6 成就模块。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.achievement import Achievement, UserAchievement
from models.submission import Submission
from models.translation import Translation
from models.user import Favorite, LearnRecord, User
from models.word import Word

# 经验值规则：行为 → 经验值
EXP_RULES: dict[str, int] = {
    "learn": 5,        # 学习一个热词
    "translate": 3,    # 翻译一次
    "correction": 20,  # 纠错通过
    "submission": 30,  # 新词条通过
    "login": 1,        # 每日登录
}

# 等级阈值：Lv1 ~ Lv10 所需累计经验
LEVEL_THRESHOLDS: list[int] = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]


class AchievementService:
    """成就服务：经验值、等级、称号与徽章。"""

    def add_experience(
        self, user_id: int, exp: int, db: Session
    ) -> dict[str, Any]:
        """增加经验值并检查等级提升。

        :param user_id: 用户 ID
        :param exp: 本次增加的经验值
        :param db: 数据库会话
        :return: {experience, old_level, new_level, leveled_up}
        """
        user = db.get(User, user_id)
        if user is None:
            raise ValueError("用户不存在")

        old_level = user.level or 1
        user.experience = (user.experience or 0) + exp
        new_level = self._compute_level(user.experience)
        user.level = new_level

        db.commit()
        return {
            "experience": user.experience,
            "old_level": old_level,
            "new_level": new_level,
            "leveled_up": new_level > old_level,
        }

    def check_unlock(self, user_id: int, db: Session) -> dict[str, Any]:
        """检查并解锁称号/徽章。

        遍历 achievements 表中所有成就，与用户当前统计比对，未解锁且满足条件则解锁。

        :param user_id: 用户 ID
        :param db: 数据库会话
        :return: {unlocked: [成就列表], stats: 用户统计}
        """
        stats = self._compute_stats(user_id, db)

        # 已解锁的成就 ID 集合
        unlocked_ids = set(
            db.execute(
                select(UserAchievement.achievement_id).where(
                    UserAchievement.user_id == user_id
                )
            )
            .scalars()
            .all()
        )

        all_achievements = db.execute(select(Achievement)).scalars().all()
        newly_unlocked: list[dict[str, Any]] = []
        for ach in all_achievements:
            if ach.id in unlocked_ids:
                continue
            if self._meets_condition(ach.condition, stats):
                db.add(
                    UserAchievement(user_id=user_id, achievement_id=ach.id)
                )
                # 解锁奖励经验值
                if ach.experience_reward:
                    self.add_experience(user_id, ach.experience_reward, db)
                newly_unlocked.append(
                    {
                        "id": ach.id,
                        "name": ach.name,
                        "type": ach.type,
                        "description": ach.description,
                        "icon": ach.icon,
                    }
                )

        db.commit()
        return {"unlocked": newly_unlocked, "stats": stats}

    def get_ranking(self, db: Session, limit: int = 50) -> list[dict[str, Any]]:
        """获取成就排行榜。

        成就点数 = title_score + badge_count * 20 + level * 30
        - title_score：已解锁称号数量 * 50
        - badge_count * 20：每个徽章 20 分
        - level * 30：当前等级 * 30 分

        :param db: 数据库会话
        :param limit: 返回数量上限
        :return: 排行榜列表，按成就点数降序
        """
        users = db.execute(select(User)).scalars().all()
        rankings: list[dict[str, Any]] = []
        for user in users:
            # 统计该用户已解锁的称号与徽章数量
            rows = (
                db.execute(
                    select(Achievement.type, func.count(UserAchievement.id))
                    .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
                    .where(UserAchievement.user_id == user.id)
                    .group_by(Achievement.type)
                )
                .all()
            )
            type_counts = {row[0]: row[1] for row in rows}
            title_count = type_counts.get("title", 0)
            badge_count = type_counts.get("badge", 0)

            title_score = title_count * 50
            score = title_score + badge_count * 20 + (user.level or 1) * 30

            rankings.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "avatar": user.avatar,
                    "level": user.level,
                    "experience": user.experience,
                    "title_count": title_count,
                    "badge_count": badge_count,
                    "achievement_score": score,
                }
            )

        rankings.sort(key=lambda x: x["achievement_score"], reverse=True)
        return rankings[:limit]

    def _compute_stats(self, user_id: int, db: Session) -> dict[str, Any]:
        """计算用户各项统计指标，用于成就条件判定。"""
        learn_count = db.execute(
            select(func.count(LearnRecord.id)).where(LearnRecord.user_id == user_id)
        ).scalar_one()
        translate_count = db.execute(
            select(func.count(Translation.id)).where(Translation.user_id == user_id)
        ).scalar_one()
        favorite_count = db.execute(
            select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        ).scalar_one()
        submission_approved = db.execute(
            select(func.count(Submission.id)).where(
                Submission.user_id == user_id, Submission.status == "approved"
            )
        ).scalar_one()

        # 连续学习天数与连续登录天数（基于学习记录日期近似）
        consecutive_learn = self._consecutive_days(
            db.execute(
                select(func.date(LearnRecord.learned_at))
                .where(LearnRecord.user_id == user_id)
                .order_by(LearnRecord.learned_at.desc())
            )
            .scalars()
            .all()
        )

        return {
            "learn_count": learn_count,
            "translate_count": translate_count,
            "favorite_count": favorite_count,
            "submission_approved": submission_approved,
            "consecutive_days": consecutive_learn,
            "consecutive_login": consecutive_learn,
            "first_translation": translate_count >= 1,
        }

    @staticmethod
    def _consecutive_days(dates: list[Any]) -> int:
        """根据日期列表计算从最近一天起连续的天数。"""
        if not dates:
            return 0
        from datetime import date, timedelta

        # 去重并按降序排序
        unique_dates: list[date] = []
        seen = set()
        for d in dates:
            if d is None or d in seen:
                continue
            seen.add(d)
            unique_dates.append(d if isinstance(d, date) else date.fromisoformat(str(d)))
        unique_dates.sort(reverse=True)

        streak = 0
        expected = date.today()
        for d in unique_dates:
            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
            elif d < expected:
                break
        return streak

    @staticmethod
    def _meets_condition(condition: dict[str, Any] | None, stats: dict[str, Any]) -> bool:
        """判断用户统计是否满足成就解锁条件。

        condition 为 JSON，如 {"learn_count": 10}、{"consecutive_days": 7}、{"first_translation": true}。
        所有键值条件需同时满足。
        """
        if not condition:
            return False
        for key, threshold in condition.items():
            actual = stats.get(key, 0)
            if isinstance(threshold, bool):
                if bool(actual) != threshold:
                    return False
            elif isinstance(threshold, (int, float)):
                if (actual or 0) < threshold:
                    return False
        return True

    @staticmethod
    def _compute_level(experience: int) -> int:
        """根据累计经验值计算等级。"""
        level = 1
        for idx, threshold in enumerate(LEVEL_THRESHOLDS):
            if experience >= threshold:
                level = idx + 1
            else:
                break
        return level
