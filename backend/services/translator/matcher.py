"""关键词匹配器

对输入文本执行长词优先、别名匹配、去重与重叠处理。
对应 SDD 5.1 关键词匹配算法。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.word import Word, WordAlias

# 关键词命中项结构
KeywordMatch = dict[str, Any]

# 投票数达到该阈值视为经多人验证，置信度为 high
HIGH_CONFIDENCE_VOTES = 10


class KeywordMatcher:
    """关键词匹配器：加载已发布词条，在文本中执行长词优先匹配。"""

    def match(self, text: str, db: Session) -> list[KeywordMatch]:
        """在文本中匹配词库词条。

        步骤：
        1. 加载所有已发布词条（含别名），按词长度降序排序
        2. 遍历词条，在文本中查找主词条与别名
        3. 处理重叠：长词优先，短词被长词完全包含则跳过
        4. 去重：同一位置取最长命中
        5. 返回 KeywordMatch 列表

        :param text: 输入文本
        :param db: 数据库会话
        :return: 命中词条列表，每项含
                 {word, position, length, source, confidence, meaning, category_id, word_id}
        """
        if not text:
            return []

        # 加载已发布词条，预加载别名
        words = (
            db.execute(
                select(Word).where(
                    Word.status == "published", Word.deleted_at.is_(None)
                )
            )
            .scalars()
            .all()
        )
        if not words:
            return []

        # 构建 候选匹配项列表：(position, length, word_id, word_text, meaning, category_id, vote_count)
        candidates: list[dict[str, Any]] = []
        for w in words:
            # 主词条匹配
            for pos in self._find_all(text, w.word):
                candidates.append(
                    self._make_candidate(
                        pos, len(w.word), w.id, w.word, w.meaning,
                        w.category_id, w.vote_count,
                    )
                )
            # 别名匹配（映射到主词条）
            aliases = (
                db.execute(
                    select(WordAlias.alias).where(WordAlias.word_id == w.id)
                )
                .scalars()
                .all()
            )
            for alias in aliases:
                if not alias:
                    continue
                for pos in self._find_all(text, alias):
                    candidates.append(
                        self._make_candidate(
                            pos, len(alias), w.id, w.word, w.meaning,
                            w.category_id, w.vote_count,
                        )
                    )

        if not candidates:
            return []

        # 按长度降序、位置升序排序，保证长词优先处理
        candidates.sort(key=lambda c: (-c["length"], c["position"]))

        # 处理重叠：长词优先，被长词完全包含的短词跳过
        kept: list[dict[str, Any]] = []
        occupied: list[tuple[int, int]] = []  # 已保留区间 (start, end)
        for cand in candidates:
            start, end = cand["position"], cand["position"] + cand["length"]
            # 当前区间是否被某个已保留区间完全包含
            if any(s <= start and end <= e for s, e in occupied):
                continue
            kept.append(cand)
            occupied.append((start, end))

        # 去重：同一 word_id 仅保留首次命中（避免主词条与别名重复）
        seen_word_ids: set[int] = set()
        result: list[KeywordMatch] = []
        for cand in kept:
            if cand["word_id"] in seen_word_ids:
                continue
            seen_word_ids.add(cand["word_id"])
            result.append(
                {
                    "word": cand["word_text"],
                    "position": cand["position"],
                    "length": cand["length"],
                    "source": "database",
                    "confidence": self._compute_confidence(cand["vote_count"]),
                    "meaning": cand["meaning"],
                    "category_id": cand["category_id"],
                    "word_id": cand["word_id"],
                }
            )

        # 按位置排序输出，便于高亮展示
        result.sort(key=lambda m: m["position"])
        return result

    @staticmethod
    def _make_candidate(
        position: int,
        length: int,
        word_id: int,
        word_text: str,
        meaning: str,
        category_id: int,
        vote_count: int,
    ) -> dict[str, Any]:
        """构造候选匹配项。"""
        return {
            "position": position,
            "length": length,
            "word_id": word_id,
            "word_text": word_text,
            "meaning": meaning,
            "category_id": category_id,
            "vote_count": vote_count,
        }

    @staticmethod
    def _find_all(text: str, sub: str) -> list[int]:
        """返回 sub 在 text 中所有出现位置的起始索引列表。"""
        if not sub:
            return []
        positions: list[int] = []
        start = 0
        while True:
            idx = text.find(sub, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + 1
        return positions

    @staticmethod
    def _compute_confidence(vote_count: int) -> str:
        """根据投票数计算置信度。

        - vote_count >= 10：high（经多人投票验证）
        - 0 < vote_count < 10：medium（投票较少）
        - vote_count == 0：medium（已发布但暂无投票）
        """
        if vote_count >= HIGH_CONFIDENCE_VOTES:
            return "high"
        return "medium"
