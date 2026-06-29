"""热词服务

每日热词推荐、用户投票、排行榜与学习历史。
对应 SDD 5.5 热词模块。
"""
from __future__ import annotations

import random
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.user import LearnRecord
from models.word import Word
from models.achievement import VoteRecord

# 每日推荐总数
DAILY_COUNT = 10
# 热门词条数量
HOT_COUNT = 7
# 随机词条数量
RANDOM_COUNT = 3
# 热度评分权重
QUERY_WEIGHT = 0.6
VOTE_WEIGHT = 0.4


class HotWordService:
    """热词服务：推荐、投票、排行、学习历史。"""

    def get_daily(self, user_id: int | None, db: Session) -> list[dict[str, Any]]:
        """获取每日热词推荐（10 个：7 热门 + 3 随机）。

        排除规则：
        - 排除该用户已学习的词条（learn_records 中存在记录）
        - 排除 risk_level=high 的词条
        - 仅取 status=published 的词条

        :param user_id: 用户 ID（游客为 None，不排除已学习）
        :param db: 数据库会话
        :return: 热词卡片列表
        """
        # 已发布、非高风险的词条
        base_query = select(Word).where(
            Word.status == "published",
            Word.deleted_at.is_(None),
            Word.risk_level != "high",
        )
        # 排除已学习词条
        if user_id is not None:
            learned_ids = (
                db.execute(
                    select(LearnRecord.word_id).where(
                        LearnRecord.user_id == user_id
                    )
                )
                .scalars()
                .all()
            )
            if learned_ids:
                base_query = base_query.where(Word.id.notin_(learned_ids))

        candidates = db.execute(base_query).scalars().all()
        if not candidates:
            return []

        # 计算热度评分：hot_score = query_count * 0.6 + vote_count * 0.4
        # 词库以 view_count 作为查询次数统计
        scored = [
            (w, self._hot_score(w)) for w in candidates
        ]
        # 按热度降序
        scored.sort(key=lambda x: x[1], reverse=True)

        # 取热门前 7
        hot = scored[:HOT_COUNT]
        # 剩余候选随机抽 3
        rest = scored[HOT_COUNT:]
        random_picks = random.sample(rest, min(RANDOM_COUNT, len(rest))) if rest else []

        result: list[dict[str, Any]] = []
        for w, score in hot + random_picks:
            result.append(self._to_card(w, score))
        return result

    def vote(
        self,
        user_id: int,
        word_id: int,
        vote_type: str,
        db: Session,
    ) -> dict[str, Any]:
        """用户对词条投票。

        :param user_id: 用户 ID
        :param word_id: 词条 ID
        :param vote_type: upvote / downvote
        :param db: 数据库会话
        :return: 投票结果
        :raises ValueError: 已投过票或词条不存在
        """
        word = db.get(Word, word_id)
        if word is None or word.deleted_at is not None:
            raise ValueError("词条不存在")

        if vote_type not in ("upvote", "downvote"):
            raise ValueError("投票类型非法")

        # 防重复：同一用户对同一词条仅可投票一次
        existing = db.execute(
            select(VoteRecord).where(
                VoteRecord.user_id == user_id, VoteRecord.word_id == word_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError("已对该词条投过票")

        # 记录投票
        record = VoteRecord(user_id=user_id, word_id=word_id, vote_type=vote_type)
        db.add(record)

        # 更新词条投票净分
        if vote_type == "upvote":
            word.vote_count = (word.vote_count or 0) + 1
        else:
            word.vote_count = (word.vote_count or 0) - 1

        db.commit()
        return {"word_id": word_id, "vote_type": vote_type, "vote_count": word.vote_count}

    def get_ranking(self, db: Session, limit: int = 50) -> list[dict[str, Any]]:
        """获取热词排行榜（按热度评分降序）。

        仅含已发布、非高风险词条。

        :param db: 数据库会话
        :param limit: 返回数量上限
        :return: 排行榜列表
        """
        words = (
            db.execute(
                select(Word)
                .where(
                    Word.status == "published",
                    Word.deleted_at.is_(None),
                    Word.risk_level != "high",
                )
                .order_by(Word.vote_count.desc(), Word.view_count.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [self._to_card(w, self._hot_score(w)) for w in words]

    def get_history(self, user_id: int, db: Session) -> list[dict[str, Any]]:
        """获取用户学习历史。

        :param user_id: 用户 ID
        :param db: 数据库会话
        :return: 学习记录列表，按学习时间降序
        """
        rows = (
            db.execute(
                select(LearnRecord, Word)
                .join(Word, LearnRecord.word_id == Word.id)
                .where(LearnRecord.user_id == user_id)
                .order_by(LearnRecord.learned_at.desc())
            )
            .all()
        )
        return [
            {
                "word_id": record.word_id,
                "word": word.word,
                "meaning": word.meaning,
                "status": record.status,
                "learned_at": record.learned_at.isoformat() if record.learned_at else None,
                "category_id": word.category_id,
                "risk_level": word.risk_level,
            }
            for record, word in rows
        ]

    @staticmethod
    def _hot_score(word: Word) -> float:
        """计算热度评分：hot_score = query_count * 0.6 + vote_count * 0.4。

        词库以 view_count 作为查询次数统计。
        """
        query_count = word.view_count or 0
        vote_count = word.vote_count or 0
        return query_count * QUERY_WEIGHT + vote_count * VOTE_WEIGHT

    @staticmethod
    def _to_card(word: Word, score: float) -> dict[str, Any]:
        """将词条转换为热词卡片结构。"""
        return {
            "word_id": word.id,
            "word": word.word,
            "pinyin": word.pinyin,
            "meaning": word.meaning,
            "example": word.example,
            "category_id": word.category_id,
            "risk_level": word.risk_level,
            "risk_types": word.risk_types,
            "risk_advice": word.risk_advice,
            "vote_count": word.vote_count,
            "view_count": word.view_count,
            "hot_score": round(score, 2),
        }
