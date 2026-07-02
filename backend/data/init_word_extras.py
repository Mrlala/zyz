"""词条详情扩展数据初始化脚本

为已存在的热门词条补充：
- Word.origin：词源说明
- WordEvolution：演化历程（不同时期的释义变迁）
- WordScene：相关使用场景

用法（在 backend/ 目录下执行）：
    python -m data.init_word_extras

脚本幂等，可重复执行：
- 已存在的 origin 字段不覆盖
- 已存在的 evolution/scene 记录不重复插入（按 word_id + period/scene_name 判重）
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保以 `python -m data.init_word_extras` 或直接运行脚本均可正确导入 backend 顶层模块
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy import select  # noqa: E402

from core.database import SessionLocal, init_db  # noqa: E402
from models.word import Word, WordEvolution, WordScene  # noqa: E402


# ---------------------------------------------------------------------------
# 热门词条的扩展数据
# ---------------------------------------------------------------------------

WORD_EXTRAS: list[dict] = [
    {
        "word": "996",
        "origin": "2019 年源自程序员社区，指早 9 点到晚 9 点每周 6 天的工作制，因 996.ICU 开源项目在 GitHub 爆火而广泛传播。",
        "evolutions": [
            {"period": "2019 年", "meaning": "程序员抗议加班的暗语，伴随 996.ICU 仓库爆火", "sort_order": 1},
            {"period": "2021 年", "meaning": "扩展为所有行业超时加班文化的代名词", "sort_order": 2},
            {"period": "当下", "meaning": "成为劳动权益与职场讨论的核心词汇，常用于批评违法用工", "sort_order": 3},
        ],
        "scenes": [
            {"scene_name": "职场沟通", "example": "他又在 996 了，周末都见不到人", "sort_order": 1},
            {"scene_name": "社交吐槽", "example": "996.ICU 仓库在 GitHub 上爆火，引发全民讨论", "sort_order": 2},
            {"scene_name": "法律讨论", "example": "996 工作制违反劳动法，可向劳动监察部门举报", "sort_order": 3},
        ],
    },
    {
        "word": "内卷",
        "origin": "2020 年从学术圈流入大众视野，原为社会学概念（克利福德·格尔茨提出），后指非理性内部竞争。",
        "evolutions": [
            {"period": "学术阶段", "meaning": "社会学概念，描述农业社会无效率的内部分化", "sort_order": 1},
            {"period": "2020 年", "meaning": "高校学生形容保研、考研中的非理性竞争", "sort_order": 2},
            {"period": "当下", "meaning": "泛指各行各业内部的过度竞争与零和博弈", "sort_order": 3},
        ],
        "scenes": [
            {"scene_name": "职场吐槽", "example": "这行业太卷了，加班都成了潜规则", "sort_order": 1},
            {"scene_name": "教育焦虑", "example": "孩子从小学就开始卷，家长也跟着累", "sort_order": 2},
        ],
    },
    {
        "word": "躺平",
        "origin": "2021 年源自网络社区，作为对内卷文化的反向回应，主张降低欲望、拒绝过度竞争。",
        "evolutions": [
            {"period": "2021 年", "meaning": "青年群体对抗内卷的态度表达", "sort_order": 1},
            {"period": "当下", "meaning": "扩展为一种生活方式选择，但也常被批评为消极避世", "sort_order": 2},
        ],
        "scenes": [
            {"scene_name": "社交吐槽", "example": "拼不动了，我选择躺平", "sort_order": 1},
            {"scene_name": "生活方式", "example": "躺平不等于不工作，而是拒绝无效内耗", "sort_order": 2},
        ],
    },
]


def seed_word_extras(session) -> None:
    """为热门词条补充 origin / evolutions / scenes 数据。"""
    added = {"origin": 0, "evolutions": 0, "scenes": 0}

    for item in WORD_EXTRAS:
        word = session.scalar(select(Word).where(Word.word == item["word"]))
        if word is None:
            print(f"  [skip] 词条不存在：{item['word']}")
            continue

        # origin：仅在为空时填充，不覆盖已有值
        if not word.origin:
            word.origin = item["origin"]
            added["origin"] += 1

        # evolutions：按 word_id + period 判重
        for ev in item["evolutions"]:
            exists = session.scalar(
                select(WordEvolution).where(
                    WordEvolution.word_id == word.id,
                    WordEvolution.period == ev["period"],
                )
            )
            if exists is None:
                session.add(
                    WordEvolution(
                        word_id=word.id,
                        period=ev["period"],
                        meaning=ev["meaning"],
                        sort_order=ev["sort_order"],
                    )
                )
                added["evolutions"] += 1

        # scenes：按 word_id + scene_name 判重
        for sc in item["scenes"]:
            exists = session.scalar(
                select(WordScene).where(
                    WordScene.word_id == word.id,
                    WordScene.scene_name == sc["scene_name"],
                )
            )
            if exists is None:
                session.add(
                    WordScene(
                        word_id=word.id,
                        scene_name=sc["scene_name"],
                        example=sc["example"],
                        sort_order=sc["sort_order"],
                    )
                )
                added["scenes"] += 1

    session.commit()
    print(f"  [done] origin 补充 {added['origin']} 条，evolutions 新增 {added['evolutions']} 条，scenes 新增 {added['scenes']} 条")


def main() -> None:
    print("=" * 60)
    print("词条详情扩展数据初始化")
    print("=" * 60)

    print("\n[1/2] 触发建表与迁移...")
    init_db()
    print("  [done] 表结构就绪")

    print("\n[2/2] 写入示例数据...")
    with SessionLocal() as session:
        seed_word_extras(session)

    print("\n" + "=" * 60)
    print("完成。可调用 GET /api/words/{id} 验证返回的 origin/evolutions/scenes 字段。")
    print("=" * 60)


if __name__ == "__main__":
    main()
