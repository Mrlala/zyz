"""AI 候选词模型

记录 AI 翻译时补充的临时词条（source=ai_temp），按出现频次累积。
频次达到阈值（默认 3 次）后自动转为 Submission 进入人工审核流程。

对应需求：用户翻译后的词进入词库（频次过滤 + 人工审核）。
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from models.base import Base


class AiWordCandidate(Base):
    """AI 候选词表：累积 AI 翻译时补充的临时词条，频次达标后转为 Submission。"""

    __tablename__ = "ai_word_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word = Column(String(100), nullable=False, comment="候选词")
    # AI 给出的临时释义，多次出现且释义不同时以 "---" 分隔追加
    meaning = Column(Text, nullable=True, comment="AI 临时释义（多次出现追加）")
    # 首次出现的原文片段（截取词前后 50 字，最多 200 字），用于审核参考
    context_sample = Column(Text, nullable=True, comment="首次出现的原文片段")
    first_seen_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="首次出现时间",
    )
    last_seen_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="最近出现时间",
    )
    occurrence_count = Column(Integer, nullable=False, default=1, comment="出现频次")
    # collecting=累积中，promoted=已转提交，discarded=已丢弃
    status = Column(
        String(10),
        nullable=False,
        default="collecting",
        comment="状态：collecting/promoted/discarded",
    )
    promoted_submission_id = Column(
        Integer, ForeignKey("submissions.id"), nullable=True, comment="转为 Submission 后的记录 ID"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )

    __table_args__ = (
        UniqueConstraint("word", name="uq_ai_word_candidates_word"),
        Index("idx_ai_candidates_status", "status"),
        Index("idx_ai_candidates_count", "occurrence_count"),
    )
