"""词条管理服务

词条 CRUD、搜索、详情查询（含多语境、别名、相关词条）与纠错提交。
对应 SDD 5.3 词条管理模块。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.category import Category
from models.submission import CorrectionReport
from models.word import Word, WordAlias, WordContext, WordRelation


class WordService:
    """词条全生命周期管理服务。"""

    def create(
        self,
        word: str,
        meaning: str,
        category_id: int,
        db: Session,
        pinyin: str | None = None,
        example: str | None = None,
        created_by: int | None = None,
    ) -> Word:
        """创建词条（用户提交，进入 pending 队列等待审核）。

        :return: 新建的词条对象
        """
        new_word = Word(
            word=word,
            pinyin=pinyin,
            meaning=meaning,
            example=example,
            category_id=category_id,
            status="pending",
            source="manual",
            created_by=created_by,
        )
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        return new_word

    def update(
        self, word_id: int, db: Session, **fields: Any
    ) -> Word:
        """更新词条字段。

        已发布词条修改后回到 pending 状态等待重新审核。

        :raises ValueError: 词条不存在
        """
        word = db.get(Word, word_id)
        if word is None or word.deleted_at is not None:
            raise ValueError("词条不存在")

        for key, value in fields.items():
            if hasattr(word, key) and value is not None:
                setattr(word, key, value)

        # 已发布词条修改后回退到 pending
        if word.status == "published":
            word.status = "pending"

        db.commit()
        db.refresh(word)
        return word

    def delete(self, word_id: int, db: Session) -> None:
        """软删除词条（置 deleted_at，保留数据用于审计）。"""
        from datetime import datetime, timezone

        word = db.get(Word, word_id)
        if word is None:
            raise ValueError("词条不存在")
        word.deleted_at = datetime.now(timezone.utc)
        word.status = "rejected"
        db.commit()

    def get(self, word_id: int, db: Session) -> Word | None:
        """按 ID 读取词条（不含关联数据）。"""
        word = db.get(Word, word_id)
        if word is None or word.deleted_at is not None:
            return None
        return word

    def get_detail(self, word_id: int, db: Session) -> dict[str, Any] | None:
        """读取词条详情，含多语境、别名、相关词条、分类。

        :return: 词条详情字典，不存在返回 None
        """
        word = db.get(Word, word_id)
        if word is None or word.deleted_at is not None:
            return None

        # 多语境
        contexts = (
            db.execute(
                select(WordContext)
                .where(WordContext.word_id == word_id)
                .order_by(WordContext.sort_order)
            )
            .scalars()
            .all()
        )
        # 别名
        aliases = (
            db.execute(select(WordAlias.alias).where(WordAlias.word_id == word_id))
            .scalars()
            .all()
        )
        # 分类
        category = db.get(Category, word.category_id) if word.category_id else None
        # 相关词条（通过 word_relations 关联）
        related_ids = (
            db.execute(
                select(WordRelation.related_word_id, WordRelation.relation_type)
                .where(WordRelation.word_id == word_id)
            )
            .all()
        )
        related: list[dict[str, Any]] = []
        if related_ids:
            rel_words = (
                db.execute(
                    select(Word).where(
                        Word.id.in_([r[0] for r in related_ids]),
                        Word.deleted_at.is_(None),
                    )
                )
                .scalars()
                .all()
            )
            rel_map = {w.id: w for w in rel_words}
            for rel_id, rel_type in related_ids:
                rw = rel_map.get(rel_id)
                if rw is None:
                    continue
                related.append(
                    {
                        "word_id": rw.id,
                        "word": rw.word,
                        "meaning": rw.meaning,
                        "relation_type": rel_type,
                    }
                )

        return {
            "id": word.id,
            "word": word.word,
            "pinyin": word.pinyin,
            "meaning": word.meaning,
            "example": word.example,
            "category_id": word.category_id,
            "category_name": category.name if category else None,
            "risk_level": word.risk_level,
            "risk_types": word.risk_types,
            "risk_advice": word.risk_advice,
            "source": word.source,
            "status": word.status,
            "confidence": word.confidence,
            "view_count": word.view_count,
            "vote_count": word.vote_count,
            "created_at": word.created_at.isoformat() if word.created_at else None,
            "contexts": [
                {
                    "id": ctx.id,
                    "context_name": ctx.context_name,
                    "meaning": ctx.meaning,
                    "sort_order": ctx.sort_order,
                }
                for ctx in contexts
            ],
            "aliases": list(aliases),
            "related": related,
        }

    def search(
        self, keyword: str, db: Session, category_id: int | None = None
    ) -> list[dict[str, Any]]:
        """按关键词与分类检索词条，支持模糊匹配。

        仅返回已发布且非软删除的词条。高风险词条仅精确匹配可见。

        :param keyword: 搜索关键词
        :param db: 数据库会话
        :param category_id: 可选分类过滤
        :return: 词条列表
        """
        if not keyword:
            return []

        query = select(Word).where(
            Word.status == "published",
            Word.deleted_at.is_(None),
        )
        # 高风险词条不出现在搜索默认结果（仅精确匹配可见）
        like_pattern = f"%{keyword}%"
        query = query.where(
            or_(
                # 精确匹配高风险词条
                (Word.word == keyword),
                # 模糊匹配非高风险词条
                ((Word.word.like(like_pattern)) | (Word.meaning.like(like_pattern)))
                & (Word.risk_level != "high"),
            )
        )
        if category_id is not None:
            query = query.where(Word.category_id == category_id)

        query = query.order_by(Word.view_count.desc())
        words = db.execute(query).scalars().all()
        return [self._to_brief(w) for w in words]

    def submit_correction(
        self,
        word_id: int,
        type: str,
        content: str,
        user_id: int,
        db: Session,
    ) -> CorrectionReport:
        """提交词条纠错报告。

        :param word_id: 被纠错词条 ID
        :param type: 纠错类型 meaning_wrong/example_wrong/outdated/other
        :param content: 纠错内容说明
        :param user_id: 提交者 ID
        :param db: 数据库会话
        :return: 纠错报告对象
        :raises ValueError: 词条不存在
        """
        word = db.get(Word, word_id)
        if word is None or word.deleted_at is not None:
            raise ValueError("词条不存在")

        if type not in ("meaning_wrong", "example_wrong", "outdated", "other"):
            raise ValueError("纠错类型非法")

        report = CorrectionReport(
            word_id=word_id,
            user_id=user_id,
            type=type,
            content=content,
            status="pending",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def _to_brief(word: Word) -> dict[str, Any]:
        """将词条转换为搜索结果简要结构。"""
        return {
            "id": word.id,
            "word": word.word,
            "pinyin": word.pinyin,
            "meaning": word.meaning,
            "category_id": word.category_id,
            "risk_level": word.risk_level,
            "vote_count": word.vote_count,
            "view_count": word.view_count,
        }
