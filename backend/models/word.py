"""词条相关模型

对应 SDD 4.4.4 ~ 4.4.7：
- Word：词条主表（软删除）
- WordAlias：词条别名表
- WordContext：多语境表
- WordRelation：词条关系表
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)

from models.base import Base, BaseModel


class Word(BaseModel):
    """词条主表，系统数据中枢，采用软删除策略。"""

    __tablename__ = "words"

    word = Column(String(100), nullable=False, comment="词条名称")
    pinyin = Column(String(100), nullable=True, comment="拼音")
    meaning = Column(Text, nullable=False, comment="释义")
    example = Column(Text, nullable=True, comment="示例语境")
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False, comment="所属分类"
    )
    risk_level = Column(
        String(10), nullable=False, default="low", comment="风险等级：low/medium/high"
    )
    risk_types = Column(JSON, nullable=True, comment='风险类型数组，如 ["法律","舆情"]')
    risk_advice = Column(Text, nullable=True, comment="使用建议")
    source = Column(
        String(10),
        nullable=False,
        default="database",
        comment="来源：database/manual/ai",
    )
    origin = Column(Text, nullable=True, comment="词源/出处说明（如源自某事件、某年网络流行）")
    status = Column(
        String(10),
        nullable=False,
        default="pending",
        comment="状态：pending/approved/rejected/published",
    )
    confidence = Column(
        String(10), nullable=True, comment="置信度：high/medium/low（AI 生成时记录）"
    )
    view_count = Column(Integer, nullable=False, default=0, comment="浏览次数")
    vote_count = Column(Integer, nullable=False, default=0, comment="投票净分（赞 - 踩）")
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="创建者（C 端用户，manual/ai 时记录）"
    )
    created_by_admin_id = Column(
        Integer, ForeignKey("admin_accounts.id"), nullable=True, comment="创建者（管理员，后台新建时记录）"
    )
    deleted_at = Column(DateTime, nullable=True, comment="软删除时间，NULL 表示未删除")

    __table_args__ = (
        Index("idx_words_category_id", "category_id"),
        Index("idx_words_status", "status"),
        Index("idx_words_risk_level", "risk_level"),
        Index("idx_words_word", "word"),
        Index("idx_words_source", "source"),
        Index("idx_words_created_at", "created_at"),
        Index("idx_words_vote_count", "vote_count"),
    )


class WordAlias(Base):
    """词条别名表，用于搜索匹配与联想推荐。"""

    __tablename__ = "word_aliases"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="所属词条")
    alias = Column(String(100), nullable=False, comment="别名")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )

    __table_args__ = (
        Index("idx_word_aliases_word_id", "word_id"),
        Index("idx_word_aliases_alias", "alias"),
    )


class WordContext(Base):
    """多语境表，存储词条在不同场景下的释义。"""

    __tablename__ = "word_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="所属词条")
    context_name = Column(
        String(50), nullable=False, comment="语境名称：直播电商/投资圈/游戏圈/日常等"
    )
    meaning = Column(Text, nullable=False, comment="该语境下的释义")
    sort_order = Column(Integer, nullable=False, default=0, comment="展示排序权重")

    __table_args__ = (Index("idx_word_contexts_word_id", "word_id"),)


class WordRelation(Base):
    """词条关系表，建立同义/相关/反义关联。"""

    __tablename__ = "word_relations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="词条 A")
    related_word_id = Column(
        Integer, ForeignKey("words.id"), nullable=False, comment="关联词条 B"
    )
    relation_type = Column(
        String(10), nullable=False, comment="关系类型：synonym/related/antonym"
    )

    __table_args__ = (
        Index("idx_word_relations_word_id", "word_id"),
        Index("idx_word_relations_related", "related_word_id"),
        UniqueConstraint(
            "word_id",
            "related_word_id",
            "relation_type",
            name="uk_word_relations",
        ),
    )


class WordEvolution(Base):
    """词条演化历程表，记录词条在不同时期的含义变迁。"""

    __tablename__ = "word_evolutions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="所属词条")
    period = Column(String(50), nullable=False, comment="时期标签：如 '2020年' / '早期' / '当下'")
    meaning = Column(Text, nullable=False, comment="该时期的释义")
    sort_order = Column(Integer, nullable=False, default=0, comment="展示排序（由远及近）")

    __table_args__ = (Index("idx_word_evolutions_word_id", "word_id"),)


class WordScene(Base):
    """词条使用场景表，记录词条典型出现的场景（如直播、职场、社交等）。"""

    __tablename__ = "word_scenes"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, comment="所属词条")
    scene_name = Column(String(50), nullable=False, comment="场景名称：如 '直播电商' / '职场沟通'")
    example = Column(Text, nullable=True, comment="该场景下的典型用例")
    sort_order = Column(Integer, nullable=False, default=0, comment="展示排序")

    __table_args__ = (Index("idx_word_scenes_word_id", "word_id"),)
