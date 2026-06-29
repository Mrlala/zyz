"""反馈服务

接收用户对翻译结果的质量反馈，与纠错模块联动，含防重复校验。
对应 SDD 5.7 反馈模块。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.feedback import Feedback
from models.submission import CorrectionReport
from models.translation import Translation
from models.word import Word

logger = logging.getLogger(__name__)

# 反馈类型
TYPE_ACCURATE = "accurate"
TYPE_INACCURATE = "inaccurate"
TYPE_OUTDATED = "outdated"


class FeedbackService:
    """质量反馈服务：accurate/inaccurate/outdated 三类处理。"""

    def submit(
        self,
        translation_id: int,
        feedback_type: str,
        comment: str | None,
        user_id: int | None,
        device_id: str | None,
        db: Session,
    ) -> dict[str, Any]:
        """提交质量反馈。

        - accurate：词条置信度权重 +1（vote_count + 1）
        - inaccurate：创建 correction_report 纠错记录
        - outdated：词条标记"待复审"（status 置回 pending）

        防重复：同一 translation_id + user_id/device_id 仅允许一次。

        :param translation_id: 翻译记录 ID
        :param feedback_type: accurate / inaccurate / outdated
        :param comment: 补充说明
        :param user_id: 用户 ID（已登录）
        :param device_id: 设备 ID（未登录用户）
        :param db: 数据库会话
        :return: 反馈结果
        :raises ValueError: 反馈类型非法、已反馈过、翻译记录不存在
        """
        if feedback_type not in (TYPE_ACCURATE, TYPE_INACCURATE, TYPE_OUTDATED):
            raise ValueError("反馈类型非法")

        if user_id is None and not device_id:
            raise ValueError("用户 ID 与设备 ID 不能同时为空")

        # 校验翻译记录存在
        translation = db.get(Translation, translation_id)
        if translation is None:
            raise ValueError("翻译记录不存在")

        # 防重复校验
        if self.has_feedbacked(translation_id, user_id, device_id, db):
            raise ValueError("您已反馈过")

        # 写入反馈记录
        feedback = Feedback(
            translation_id=translation_id,
            user_id=user_id,
            device_id=device_id,
            type=feedback_type,
            comment=comment,
        )
        db.add(feedback)

        # 按类型联动处理
        word_ids = self._extract_word_ids(translation)
        if feedback_type == TYPE_ACCURATE:
            self._adjust_confidence(word_ids, db)
        elif feedback_type == TYPE_INACCURATE:
            self._create_correction_reports(
                word_ids, user_id, comment, db
            )
        elif feedback_type == TYPE_OUTDATED:
            self._mark_for_review(word_ids, db)

        db.commit()
        return {
            "translation_id": translation_id,
            "feedback_type": feedback_type,
            "status": "submitted",
        }

    def has_feedbacked(
        self,
        translation_id: int,
        user_id: int | None,
        device_id: str | None,
        db: Session,
    ) -> bool:
        """校验是否已对该翻译记录反馈过（防重复）。

        已登录用户按 user_id 判定，未登录用户按 device_id 判定。
        """
        if user_id is not None:
            exists = db.execute(
                select(Feedback.id).where(
                    Feedback.translation_id == translation_id,
                    Feedback.user_id == user_id,
                )
            ).scalar_one_or_none()
        else:
            exists = db.execute(
                select(Feedback.id).where(
                    Feedback.translation_id == translation_id,
                    Feedback.device_id == device_id,
                )
            ).scalar_one_or_none()
        return exists is not None

    @staticmethod
    def _extract_word_ids(translation: Translation) -> list[int]:
        """从翻译结果 JSON 中提取命中的词库词条 ID。"""
        result = translation.result or {}
        keywords = result.get("keywords", []) or []
        word_ids: list[int] = []
        for kw in keywords:
            wid = kw.get("word_id")
            if wid is not None:
                word_ids.append(wid)
        return word_ids

    @staticmethod
    def _adjust_confidence(word_ids: list[int], db: Session) -> None:
        """accurate 反馈：词条置信度权重 +1（以 vote_count 作为置信度权重）。"""
        if not word_ids:
            return
        words = db.execute(select(Word).where(Word.id.in_(word_ids))).scalars().all()
        for word in words:
            word.vote_count = (word.vote_count or 0) + 1

    @staticmethod
    def _create_correction_reports(
        word_ids: list[int],
        user_id: int | None,
        comment: str | None,
        db: Session,
    ) -> None:
        """inaccurate 反馈：为关联词条创建纠错报告。"""
        if not word_ids:
            return
        # 用户 ID 必填，纠错报告 user_id 不可空
        if user_id is None:
            return
        for word_id in word_ids:
            report = CorrectionReport(
                word_id=word_id,
                user_id=user_id,
                type="meaning_wrong",
                content=comment or "用户反馈翻译不准确",
                status="pending",
            )
            db.add(report)

    @staticmethod
    def _mark_for_review(word_ids: list[int], db: Session) -> None:
        """outdated 反馈：词条标记"待复审"（status 置回 pending 进入复审队列）。"""
        if not word_ids:
            return
        words = db.execute(select(Word).where(Word.id.in_(word_ids))).scalars().all()
        for word in words:
            word.status = "pending"
