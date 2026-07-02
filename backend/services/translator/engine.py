"""翻译引擎

协调词库优先策略与 AI 生成，组装最终的七模块结构化翻译结果。
对应 SDD 5.1 翻译引擎模块。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.word import WordContext
from services.ai.client import AIClient, InsufficientBalanceError
from services.ai.fallback import FallbackHandler
from services.translator.matcher import KeywordMatcher, KeywordMatch

logger = logging.getLogger(__name__)


class TranslationEngine:
    """翻译引擎：词库匹配 → AI 生成 → 结果组装，含降级策略。"""

    def __init__(self) -> None:
        self.matcher = KeywordMatcher()
        self.ai_client = AIClient()
        self.fallback = FallbackHandler()

    async def translate(self, text: str, mode: str, db: Session) -> dict[str, Any]:
        """主翻译入口。

        :param text: 待翻译原文
        :param mode: 翻译模式（dict/translate）
        :param db: 数据库会话
        :return: 结构化翻译结果
                 {translation, keywords[], context, subtext, suggestion,
                  suggested_reply, risk, related, fallback}
        """
        if not text or not text.strip():
            return self._empty_result()

        # 第一步：关键词匹配（词库优先）
        matched_words = self.match_keywords(text, db)

        # 第二步：多语境处理，补充/调整命中词条释义
        matched_words = self._enrich_with_contexts(text, matched_words, db)

        # 【短路】词库命中且为短词/短语时，直接返回，不调 AI（省额度、低延迟）
        if matched_words and self._is_short_phrase(text):
            return self._build_dict_only_result(text, matched_words)

        # 第三步：未命中或长句，调用 AI 生成结构化结果
        try:
            ai_result = await self.ai_client.translate(text, matched_words, db)
            return self.build_result(text, matched_words, ai_result)
        except InsufficientBalanceError as exc:
            # 余额不足：明确提示并降级到词库模式
            logger.error("DeepSeek 余额不足，触发降级: %s", exc)
            fallback_result = self.fallback.handle(text, matched_words, exc)
            fallback_result["fallback_reason"] = "insufficient_balance"
            return fallback_result
        except Exception as exc:  # noqa: BLE001 捕获所有 AI 异常以触发降级
            logger.warning("AI 调用失败，触发降级: %s", exc)
            fallback_result = self.fallback.handle(text, matched_words, exc)
            return fallback_result

    def match_keywords(self, text: str, db: Session) -> list[KeywordMatch]:
        """关键词匹配：长词优先 + 别名匹配 + 去重 + 重叠处理。

        委托给 KeywordMatcher 实现。
        """
        return self.matcher.match(text, db)

    def build_result(
        self,
        text: str,
        matched_words: list[KeywordMatch],
        ai_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """组装最终结果：合并词库命中 + AI 生成内容。

        - 词库命中词条 source="database"
        - AI 补充词条 source="ai_temp"
        - 多语境无数据时由 AI 补充，标记 ai_temp
        """
        if ai_result is None:
            ai_result = {}

        # 合并关键词：词库命中优先，AI 补充的去重后加入
        db_words = {m["word"] for m in matched_words}
        keywords: list[dict[str, Any]] = []
        # 词库命中项保留完整字段
        for m in matched_words:
            keywords.append(
                {
                    "word": m["word"],
                    "meaning": m["meaning"],
                    "source": "database",
                    "confidence": m["confidence"],
                    "position": m["position"],
                    "length": m["length"],
                    "category_id": m.get("category_id"),
                    "word_id": m.get("word_id"),
                }
            )
        # AI 返回的关键词中，未命中词库的标记为 ai_temp
        for kw in ai_result.get("keywords", []) or []:
            word = kw.get("word", "")
            if not word or word in db_words:
                continue
            keywords.append(
                {
                    "word": word,
                    "meaning": kw.get("meaning", ""),
                    "source": "ai_temp",
                    "confidence": kw.get("confidence", "medium"),
                    "position": None,
                    "length": None,
                    "category_id": None,
                    "word_id": None,
                }
            )
            db_words.add(word)

        risk = ai_result.get("risk") or {
            "risk_level": "low",
            "risk_types": [],
            "advice": "",
        }

        return {
            "translation": ai_result.get("translation", ""),
            "keywords": keywords,
            "context": ai_result.get("context", "未知"),
            "subtext": ai_result.get("subtext", ""),
            "suggestion": ai_result.get("suggestion", ""),
            "suggested_reply": ai_result.get("suggested_reply", ""),
            "risk": {
                "risk_level": risk.get("risk_level", "low"),
                "risk_types": risk.get("risk_types", []),
                "advice": risk.get("advice", ""),
            },
            "related": ai_result.get("related", []),
            "fallback": False,
        }

    def _enrich_with_contexts(
        self,
        text: str,
        matched_words: list[KeywordMatch],
        db: Session,
    ) -> list[KeywordMatch]:
        """多语境处理：查询 word_contexts 表，无数据时标记需 AI 补充。

        - 命中明确场景标记 → 采用对应语境释义
        - 无语境数据 → 标记 source 保持 database，但 meaning 不变，
          由 AI 在生成时补充多语境候选（写入 word_contexts 由上层流程处理）
        """
        if not matched_words:
            return matched_words

        word_ids = [m["word_id"] for m in matched_words if m.get("word_id")]
        if not word_ids:
            return matched_words

        # 一次性查询所有命中词条的多语境
        contexts = (
            db.execute(
                select(WordContext).where(WordContext.word_id.in_(word_ids))
            )
            .scalars()
            .all()
        )
        # 按 word_id 分组
        context_map: dict[int, list[WordContext]] = {}
        for ctx in contexts:
            context_map.setdefault(ctx.word_id, []).append(ctx)

        for m in matched_words:
            wid = m.get("word_id")
            if not wid:
                continue
            ctxs = context_map.get(wid)
            if not ctxs:
                # 无语境数据：标记需 AI 补充（不修改 meaning，由 AI 生成多语境）
                m["needs_ai_context"] = True
                continue
            m["needs_ai_context"] = False
            # 尝试根据文本特征推断当前语境
            inferred = self._infer_context(ctxs, text)
            if inferred is not None:
                m["meaning"] = inferred.meaning
                m["context_name"] = inferred.context_name

        return matched_words

    @staticmethod
    def _infer_context(
        contexts: list[WordContext], text: str
    ) -> WordContext | None:
        """根据文本特征推断当前语境，选择最匹配的语境释义。

        - 命中明确场景标记（语境名称出现在文本中）→ 返回对应语境
        - 无明确场景 → 返回 sort_order 最小的默认语境
        """
        # 优先匹配语境名称出现在文本中的
        for ctx in contexts:
            if ctx.context_name and ctx.context_name in text:
                return ctx
        # 无明确命中，取排序最靠前的作为默认语境
        return min(contexts, key=lambda c: c.sort_order)

    @staticmethod
    def _is_short_phrase(text: str) -> bool:
        """判断是否短词/短语：长度 ≤ 8 且 无标点（中英文标点均判定）。

        用于决定词库命中后是否短路返回（不调 AI）。
        """
        import re

        t = text.strip()
        if not t:
            return False
        if len(t) > 8:
            return False
        # 含标点视为句子，不走短路
        if re.search(r"[，。！？；,;.!?()\[\]【】、\s]", t):
            return False
        return True

    def _build_dict_only_result(
        self, text: str, matched_words: list[KeywordMatch]
    ) -> dict[str, Any]:
        """词库命中短路：用词库数据组装完整结果，不调 AI。

        - translation：拼接各命中词条释义
        - subtext/suggestion/suggested_reply：空（短词无需）
        - risk：默认 low（词条级风险由详情页展示）
        - related/context：空（由详情页展示）
        """
        keywords: list[dict[str, Any]] = []
        meaning_parts: list[str] = []
        for m in matched_words:
            keywords.append(
                {
                    "word": m["word"],
                    "meaning": m["meaning"],
                    "source": "database",
                    "confidence": m["confidence"],
                    "position": m["position"],
                    "length": m["length"],
                    "category_id": m.get("category_id"),
                    "word_id": m.get("word_id"),
                    "is_favorited": False,
                }
            )
            meaning_parts.append(f"{m['word']}：{m['meaning']}")

        translation = "；".join(meaning_parts) if meaning_parts else ""

        return {
            "translation": translation,
            "keywords": keywords,
            "context": "",
            "subtext": "",
            "suggestion": "",
            "suggested_reply": "",
            "risk": {"risk_level": "low", "risk_types": [], "advice": ""},
            "related": [],
            "fallback": False,
            "dict_only": True,  # 标记：纯词库返回（前端可用于隐藏建议回复等）
        }

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        """空文本返回的空结果。"""
        return {
            "translation": "",
            "keywords": [],
            "context": "未知",
            "subtext": "",
            "suggestion": "",
            "suggested_reply": "",
            "risk": {"risk_level": "low", "risk_types": [], "advice": ""},
            "related": [],
            "fallback": False,
        }
