"""敏感词过滤模块

对用户输入侧（翻译/提交/反馈/纠错）进行敏感词检测，命中则拒绝并提示。

设计考量：
- 轻量级：基于关键词集合的 contains 匹配，不引入 DFA 算法库
- 可配置：敏感词列表从 data/sensitive_words.txt 加载，每行一个词
- 可扩展：若词库增大至万级以上，建议升级为 Aho-Corasick 算法
- 隐私保护：仅记录命中次数，不记录原文与命中词
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# 默认敏感词库路径
_DEFAULT_WORDS_FILE = Path(__file__).resolve().parent.parent / "data" / "sensitive_words.txt"

# 内置基础敏感词（文件不存在或为空时使用）
_FALLBACK_WORDS: set[str] = {
    # 政治敏感
    "反动", "颠覆",
    # 违法
    "毒品交易", "贩毒", "洗钱",
    # 色情（仅示例，实际词库应更完整）
    "色情服务", "裸聊",
    # 其他
    "自杀方法", "炸弹制作",
}

# 敏感词集合（小写）
_sensitive_words: set[str] = set()

# 是否已加载
_loaded = False


def load_sensitive_words(words_file: Path | str | None = None) -> int:
    """加载敏感词库。

    :param words_file: 敏感词文件路径，None 则用默认路径
    :return: 加载的敏感词数量
    """
    global _sensitive_words, _loaded

    file_path = Path(words_file) if words_file else _DEFAULT_WORDS_FILE
    words: set[str] = set()

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        words.add(word)
            logger.info("从 %s 加载 %d 个敏感词", file_path, len(words))
        except Exception as exc:
            logger.warning("加载敏感词文件 %s 失败: %s，使用内置词库", file_path, exc)

    if not words:
        words = _FALLBACK_WORDS.copy()
        logger.info("使用内置敏感词库，共 %d 个", len(words))

    _sensitive_words = words
    _loaded = True
    return len(words)


def get_sensitive_words() -> set[str]:
    """获取当前敏感词集合（未加载则先加载）。"""
    if not _loaded:
        load_sensitive_words()
    return _sensitive_words


def contains_sensitive(text: str) -> bool:
    """检测文本是否包含敏感词。

    :param text: 待检测文本
    :return: True 表示包含敏感词
    """
    if not text:
        return False
    if not _loaded:
        load_sensitive_words()
    lower_text = text.lower()
    for word in _sensitive_words:
        if word in lower_text:
            return True
    return False


def find_sensitive(text: str) -> list[str]:
    """查找文本中命中的敏感词列表（用于日志记录，不返回原文）。

    :param text: 待检测文本
    :return: 命中的敏感词列表
    """
    if not text:
        return []
    if not _loaded:
        load_sensitive_words()
    lower_text = text.lower()
    return [word for word in _sensitive_words if word in lower_text]


def is_sensitive_filter_enabled() -> bool:
    """检查敏感词过滤是否启用（可通过环境变量 SENSITIVE_FILTER_ENABLED=off 关闭）。"""
    return os.getenv("SENSITIVE_FILTER_ENABLED", "on").lower() in ("on", "1", "true", "yes")
