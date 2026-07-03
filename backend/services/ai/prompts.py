"""Prompt 模板

构造翻译任务的 System Prompt 与 User Prompt，约束大模型输出结构化 JSON。
对应 SDD 5.2 Prompt 模板设计。

System Prompt 支持数据库覆盖：从 system_configs.translate_system_prompt 读取，
无配置时回退到代码中的默认值 DEFAULT_SYSTEM_PROMPT。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 关键词匹配项类型：{word, position, length, source, confidence, meaning, category_id, word_id}
KeywordMatch = dict[str, Any]


# 默认 System Prompt：数据库无配置时使用此值
DEFAULT_SYSTEM_PROMPT = """你是一位中文语境翻译专家，擅长把网络黑话、职场话术、社交俚语翻译为通俗易懂的现代汉语。

【角色设定】
- 你精通当代中文互联网语境、职场黑话、社交潜台词
- 你能识别字面意思背后的真实意图（潜台词）
- 你能根据语境判断风险（冒犯性、敏感性、合规性）

【输出格式】
必须严格输出 JSON，符合以下结构，不要输出任何 JSON 之外的文本，也不要使用 markdown 代码块包裹：
{
  "translation": "通俗翻译（自然流畅的现代汉语）",
  "keywords": [
    {"word": "词条", "meaning": "释义", "source": "database|ai_temp", "confidence": "high|medium|low"}
  ],
  "context": "场景识别（职场/社交/网络/技术/生活/其他）",
  "subtext": "潜台词解读",
  "suggestion": "行动建议",
  "suggested_reply": "建议回复话术（不超过50字，需与场景匹配）",
  "risk": {"risk_level": "low|medium|high", "risk_types": ["风险类型"], "advice": "使用建议"},
  "related": ["相关词条"]
}

【约束条件】
1. translation 必须是自然流畅的现代汉语，不能直接复述原话
2. 如词库命中词条已给出 meaning，翻译时优先采纳并融合
3. risk.risk_level 为 high 时 advice 不能为空
4. suggested_reply 必须与 context 场景匹配，长度不超过 50 字
5. keywords 数组中已命中词库的词条 source 用 "database"，AI 补充的用 "ai_temp"
6. 不允许输出 markdown 代码块包裹，必须直接输出 JSON"""

# 向后兼容：外部模块引用 SYSTEM_PROMPT 的保持可用
SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT


def get_system_prompt(db: Session) -> str:
    """从数据库读取当前配置的 System Prompt，无配置时回退默认值。

    :param db: 数据库会话
    :return: System Prompt 字符串
    """
    try:
        from models.admin import SystemConfig

        cfg = db.execute(
            select(SystemConfig).where(SystemConfig.config_key == "translate_system_prompt")
        ).scalar_one_or_none()
        if cfg and cfg.config_value:
            return cfg.config_value
    except Exception as exc:
        logger.warning("读取 translate_system_prompt 配置失败，回退默认值: %s", exc)
    return DEFAULT_SYSTEM_PROMPT


def _format_matched_words(matched_words: list[KeywordMatch]) -> str:
    """将已匹配的词库词条格式化为列表文本。"""
    if not matched_words:
        return "（无命中的词库词条）"
    lines = []
    for item in matched_words:
        lines.append(
            f"- 词条：{item.get('word', '')}\n"
            f"  释义：{item.get('meaning', '')}\n"
            f"  分类ID：{item.get('category_id', '')}\n"
            f"  置信度：{item.get('confidence', '')}"
        )
    return "\n".join(lines)


def BUILD_TRANSLATE_PROMPT(
    text: str, matched_words: list[KeywordMatch], db: Session | None = None
) -> tuple[str, str]:
    """构建翻译任务的 System + User Prompt。

    :param text: 待翻译原文
    :param matched_words: 关键词匹配器命中的词库词条列表
    :param db: 数据库会话，传入时从 system_configs 读取自定义 Prompt，否则用默认值
    :return: (system_prompt, user_prompt) 二元组
    """
    system_prompt = get_system_prompt(db) if db is not None else DEFAULT_SYSTEM_PROMPT
    user_prompt = (
        "【待翻译原文】\n"
        f"{text}\n\n"
        "【已命中的词库词条】\n"
        f"{_format_matched_words(matched_words)}\n\n"
        "请基于以上信息输出符合 System Prompt 约定的 JSON。"
    )
    return system_prompt, user_prompt
