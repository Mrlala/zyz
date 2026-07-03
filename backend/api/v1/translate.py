"""翻译接口

对应 SDD 4.5.3：
- POST /translate：中译中翻译（调用 TranslationEngine）
- POST /translate/dict：词典模式匹配
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_device_id
from core.database import get_db
from core.sensitive_filter import contains_sensitive, is_sensitive_filter_enabled
from models.ai_candidate import AiWordCandidate
from models.category import Category
from models.submission import Submission
from models.translation import Translation
from models.user import User
from models.word import Word
from schemas import BaseResponse, DictRequest, TranslateRequest
from services.translator.engine import TranslationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translate", tags=["翻译"])

# AI 候选词频次阈值：达到该次数后自动转为 Submission 进入人工审核
AI_CANDIDATE_PROMOTE_THRESHOLD = 3


def _extract_context_sample(text: str, word: str, radius: int = 50) -> str:
    """截取原文中该词前后各 radius 字的片段，用于审核参考。"""
    idx = text.find(word)
    if idx < 0:
        return text[:200]
    start = max(0, idx - radius)
    end = min(len(text), idx + len(word) + radius)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet[:200]


def _record_ai_candidates(result: dict, original_text: str, db: Session) -> None:
    """记录 AI 补充的临时词条到候选词表，频次达标后自动转为 Submission。

    隐私保护：context_sample 仅截取词前后 50 字，不存全文。
    去重：已存在 ai_word_candidates / words(published) / submissions(pending) 的词跳过。
    """
    keywords = result.get("keywords") or []
    ai_temp_words = [k for k in keywords if k.get("source") == "ai_temp"]
    if not ai_temp_words:
        return

    # 获取默认分类（取第一个分类作为 AI 候选词的默认分类）
    default_category = db.execute(select(Category).limit(1)).scalar_one_or_none()
    if default_category is None:
        logger.warning("无分类数据，AI 候选词无法转 Submission，仅记录候选词")

    for kw in ai_temp_words:
        word_text = (kw.get("word") or "").strip()
        if not word_text:
            continue
        meaning_text = (kw.get("meaning") or "").strip()

        # 1. 查 ai_word_candidates 是否已存在
        existing = db.execute(
            select(AiWordCandidate).where(AiWordCandidate.word == word_text)
        ).scalar_one_or_none()

        if existing is not None:
            if existing.status != "collecting":
                continue  # 已转提交或已丢弃
            existing.occurrence_count += 1
            existing.last_seen_at = datetime.now(timezone.utc)
            # 释义不同则追加
            if meaning_text and meaning_text not in (existing.meaning or ""):
                existing.meaning = f"{existing.meaning or ''}---{meaning_text}".strip("---")
            # 频次达标自动转 Submission
            if existing.occurrence_count >= AI_CANDIDATE_PROMOTE_THRESHOLD and default_category is not None:
                _promote_candidate(existing, default_category.id, db)
            continue

        # 2. 新词：检查是否已在 words(published) 或 submissions(pending)
        in_words = db.execute(
            select(Word.id).where(Word.word == word_text, Word.status == "published", Word.deleted_at.is_(None)).limit(1)
        ).first()
        if in_words:
            continue  # 词库已有，跳过
        in_submissions = db.execute(
            select(Submission.id).where(Submission.word == word_text, Submission.status == "pending").limit(1)
        ).first()
        if in_submissions:
            continue  # 已有待审核提交，跳过

        # 3. 插入候选词
        candidate = AiWordCandidate(
            word=word_text,
            meaning=meaning_text or None,
            context_sample=_extract_context_sample(original_text, word_text),
            occurrence_count=1,
            status="collecting",
        )
        db.add(candidate)


def _promote_candidate(candidate: AiWordCandidate, category_id: int, db: Session) -> None:
    """将候选词转为 Submission 进入人工审核流程。"""
    # 取最后一次的释义（按 --- 分隔后取最后一段）
    meaning = candidate.meaning or "AI 自动补充词条"
    if "---" in meaning:
        meaning = meaning.split("---")[-1].strip()

    submission = Submission(
        user_id=None,  # 系统提交
        word=candidate.word,
        meaning=meaning,
        category_id=category_id,
        status="pending",
    )
    db.add(submission)
    db.flush()  # 获取 submission.id
    candidate.status = "promoted"
    candidate.promoted_submission_id = submission.id
    logger.info("AI 候选词 '%s' 频次达 %d，已转为 Submission #%d",
                candidate.word, candidate.occurrence_count, submission.id)


@router.post("", response_model=BaseResponse)
async def translate(
    request: TranslateRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    device_id: str | None = Depends(get_device_id),
) -> BaseResponse:
    """中译中翻译。

    调用 TranslationEngine 完成词库匹配 + AI 生成，返回结构化翻译结果。
    认证可选：已认证用户可触发反馈开关并记录翻译历史。
    """
    if request.mode not in ("translate", "dict"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mode 取值非法，仅支持 translate/dict",
        )

    # 敏感词过滤：命中则拒绝，不消耗 AI 调用
    if is_sensitive_filter_enabled() and contains_sensitive(request.text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="输入内容包含敏感词，请修改后重试",
        )

    engine = TranslationEngine()
    result = await engine.translate(request.text, request.mode, db)

    # 记录翻译历史，便于反馈关联
    # original_text_hash 用于后台聚合统计而不暴露用户原文（隐私保护）
    text_hash = hashlib.sha256(request.text.encode("utf-8")).hexdigest()
    translation_record = Translation(
        user_id=user.id if user else None,
        original_text=request.text,
        original_text_hash=text_hash,
        result=result,
        mode=request.mode,
    )
    db.add(translation_record)
    # 记录 AI 补充的临时词条到候选词表（频次达 3 次自动转 Submission）
    try:
        _record_ai_candidates(result, request.text, db)
    except Exception as exc:
        logger.warning("记录 AI 候选词失败（不影响翻译结果）: %s", exc)
    db.commit()
    db.refresh(translation_record)

    # 已认证用户允许反馈
    result["feedback_enabled"] = user is not None
    result["translation_id"] = translation_record.id
    return BaseResponse(data=result)


@router.post("/dict", response_model=BaseResponse)
async def translate_dict(
    request: DictRequest,
    db: Session = Depends(get_db),
) -> BaseResponse:
    """词典模式匹配。

    直接对输入文本执行词库匹配，返回命中词条列表。
    """
    engine = TranslationEngine()
    matches = engine.match_keywords(request.text, db)

    hits = [
        {
            "id": m.get("word_id"),
            "word": m.get("word", ""),
            "pinyin": None,
            "definition": m.get("meaning", ""),
            "tags": [],
            "match_score": 1.0 if m.get("source") == "database" else 0.8,
        }
        for m in matches
    ]

    if not hits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未命中任何词条",
        )

    return BaseResponse(data={"hits": hits, "total": len(hits)})
