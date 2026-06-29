"""初始化数据脚本

用法（在 backend/ 目录下执行）：
    python -m data.init_data

功能：
    1. 创建所有数据库表
    2. 插入 12 个一级分类
    3. 插入 3 个测试用户（admin / tester01 / tester02，密码均为 123456）
    4. 插入 10 个初始成就配置
    5. 插入 20 个示例词条（覆盖各分类，含完整字段）

脚本幂等，可重复执行：已存在的记录会被跳过。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 确保以 `python -m data.init_data` 或直接运行脚本均可正确导入 backend 顶层模块
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy import select  # noqa: E402

from core.database import SessionLocal, init_db  # noqa: E402
from core.security import hash_password  # noqa: E402
from models import Achievement, Category, User, Word  # noqa: E402


# ---------------------------------------------------------------------------
# 初始数据定义
# ---------------------------------------------------------------------------

# 12 个一级分类
CATEGORIES: list[dict[str, Any]] = [
    {"name": "职场黑话", "icon": "workplace", "sort_order": 10},
    {"name": "互联网梗", "icon": "meme", "sort_order": 20},
    {"name": "直播电商", "icon": "live", "sort_order": 30},
    {"name": "游戏术语", "icon": "game", "sort_order": 40},
    {"name": "饭圈用语", "icon": "fan", "sort_order": 50},
    {"name": "学术黑话", "icon": "academic", "sort_order": 60},
    {"name": "金融投资", "icon": "finance", "sort_order": 70},
    {"name": "医疗健康", "icon": "medical", "sort_order": 80},
    {"name": "法律术语", "icon": "legal", "sort_order": 90},
    {"name": "科技数码", "icon": "tech", "sort_order": 100},
    {"name": "生活方式", "icon": "lifestyle", "sort_order": 110},
    {"name": "社交网络", "icon": "social", "sort_order": 120},
]

# 3 个测试用户（密码统一为 123456，bcrypt 哈希）
USERS: list[dict[str, Any]] = [
    {
        "username": "admin",
        "nickname": "管理员",
        "password": "123456",
        "level": 99,
        "title": "系统管理员",
        "experience": 0,
    },
    {
        "username": "tester01",
        "nickname": "测试用户01",
        "password": "123456",
        "level": 1,
        "experience": 0,
    },
    {
        "username": "tester02",
        "nickname": "测试用户02",
        "password": "123456",
        "level": 1,
        "experience": 0,
    },
]

# 10 个初始成就配置（来自 SDD 4.4.19）
ACHIEVEMENTS: list[dict[str, Any]] = [
    {
        "name": "初窥门径",
        "description": "学习首个词条",
        "type": "title",
        "condition": {"learn_count": 1},
        "experience_reward": 10,
        "icon": "beginner",
    },
    {
        "name": "小有所成",
        "description": "学习 10 个词条",
        "type": "badge",
        "condition": {"learn_count": 10},
        "experience_reward": 50,
        "icon": "learner",
    },
    {
        "name": "博学多识",
        "description": "学习 50 个词条",
        "type": "title",
        "condition": {"learn_count": 50},
        "experience_reward": 200,
        "icon": "scholar",
    },
    {
        "name": "热词达人",
        "description": "学习 100 个词条",
        "type": "title",
        "condition": {"learn_count": 100},
        "experience_reward": 500,
        "icon": "master",
    },
    {
        "name": "收藏家",
        "description": "收藏 20 个词条",
        "type": "badge",
        "condition": {"favorite_count": 20},
        "experience_reward": 100,
        "icon": "collector",
    },
    {
        "name": "贡献者",
        "description": "首次提交词条",
        "type": "badge",
        "condition": {"submit_count": 1},
        "experience_reward": 30,
        "icon": "contributor",
    },
    {
        "name": "优质贡献者",
        "description": "5 个提交通过审核",
        "type": "title",
        "condition": {"submit_approved": 5},
        "experience_reward": 200,
        "icon": "quality_contributor",
    },
    {
        "name": "纠错先锋",
        "description": "提交 3 次纠错",
        "type": "badge",
        "condition": {"correction_count": 3},
        "experience_reward": 80,
        "icon": "corrector",
    },
    {
        "name": "翻译达人",
        "description": "翻译 50 次",
        "type": "badge",
        "condition": {"translate_count": 50},
        "experience_reward": 100,
        "icon": "translator",
    },
    {
        "name": "资深用户",
        "description": "累计登录 30 天",
        "type": "title",
        "condition": {"login_days": 30},
        "experience_reward": 300,
        "icon": "veteran",
    },
]

# 20 个示例词条，覆盖全部 12 个分类，含完整字段
# category 字段为分类名称，插入时解析为 category_id
WORDS: list[dict[str, Any]] = [
    {
        "word": "内卷",
        "pinyin": "nèi juǎn",
        "meaning": "指非理性的内部竞争，同侪之间为争夺有限资源不断加码投入，导致整体收益不变甚至下降。",
        "example": "现在这行业太卷了，大家都主动加班，纯粹是内卷。",
        "category": "职场黑话",
        "risk_level": "high",
        "risk_types": ["舆情", "价值观"],
        "risk_advice": "使用时注意语境，避免渲染消极竞争情绪。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 1280,
        "vote_count": 56,
    },
    {
        "word": "躺平",
        "pinyin": "tǎng píng",
        "meaning": "指不再渴求世俗成功、主动降低欲望与付出，以最低消耗维持生活。",
        "example": "拼不动了，我选择躺平，做条咸鱼也挺好。",
        "category": "职场黑话",
        "risk_level": "medium",
        "risk_types": ["舆情", "价值观"],
        "risk_advice": "易引发消极解读，官方场合慎用。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 980,
        "vote_count": 42,
    },
    {
        "word": "996",
        "pinyin": "jiǔ jiǔ liù",
        "meaning": "指早 9 点上班、晚 9 点下班、每周工作 6 天的高强度加班制度。",
        "example": "公司实行 996，身体真的吃不消。",
        "category": "职场黑话",
        "risk_level": "high",
        "risk_types": ["法律", "舆情"],
        "risk_advice": "涉及违法用工风险，引用时须结合法律语境说明。",
        "source": "database",
        "status": "published",
        "confidence": "high",
        "view_count": 2100,
        "vote_count": 88,
    },
    {
        "word": "打工人",
        "pinyin": "dǎ gōng rén",
        "meaning": "上班族对自身身份的自嘲式称呼，带有幽默与辛酸并存的情绪色彩。",
        "example": "打工人，打工魂，打工都是人上人。",
        "category": "职场黑话",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "中性偏幽默，通用场景可用。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 670,
        "vote_count": 31,
    },
    {
        "word": "YYDS",
        "pinyin": "yóng yǒng dì shén",
        "meaning": "“永远的神”拼音首字母缩写，用于表达对某人或某物的极高赞美。",
        "example": "这家店的奶茶 YYDS！",
        "category": "互联网梗",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "通用赞美用语，无特殊风险。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 1540,
        "vote_count": 73,
    },
    {
        "word": "绝绝子",
        "pinyin": "jué jué zǐ",
        "meaning": "表示极好或极差的程度副词性短语，多用于夸张赞叹。",
        "example": "这个妆容绝绝子，太好看了吧！",
        "category": "互联网梗",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "网络流行语，注意场合。",
        "source": "ai",
        "status": "published",
        "confidence": "medium",
        "view_count": 820,
        "vote_count": 25,
    },
    {
        "word": "破防",
        "pinyin": "pò fáng",
        "meaning": "原指游戏防御被击破，现指心理防线被击溃、情绪被触动。",
        "example": "看到那段视频我直接破防了，眼泪止不住。",
        "category": "互联网梗",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "情感表达用语，无特殊风险。",
        "source": "database",
        "status": "published",
        "confidence": "high",
        "view_count": 1100,
        "vote_count": 48,
    },
    {
        "word": "宝子们",
        "pinyin": "bǎo zǐ men",
        "meaning": "直播带货主播对观众的亲昵称呼，源于“宝贝”的变体。",
        "example": "宝子们，今天给大家带来一波福利！",
        "category": "直播电商",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "亲昵称呼，营造氛围用，无特殊风险。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 760,
        "vote_count": 22,
    },
    {
        "word": "321上链接",
        "pinyin": "sān èr yī shàng liàn jiē",
        "meaning": "直播带货倒计时后上架商品链接的话术，营造紧迫感促成下单。",
        "example": "准备好了吗？321 上链接！",
        "category": "直播电商",
        "risk_level": "medium",
        "risk_types": ["消费诱导"],
        "risk_advice": "涉嫌制造冲动消费，引用时需提示理性消费。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 1340,
        "vote_count": 39,
    },
    {
        "word": "AFK",
        "pinyin": "ā yōu ef kèi",
        "meaning": "“Away From Keyboard”缩写，指玩家暂时离开键盘、挂机不在状态。",
        "example": "我去倒杯水，AFK 一下。",
        "category": "游戏术语",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "通用游戏术语，无特殊风险。",
        "source": "database",
        "status": "published",
        "confidence": "high",
        "view_count": 540,
        "vote_count": 18,
    },
    {
        "word": "躺赢",
        "pinyin": "tǎng yíng",
        "meaning": "指不费力就能获胜，多用于游戏或团队场景中被队友带飞。",
        "example": "这局遇到大神带飞，直接躺赢。",
        "category": "游戏术语",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "中性游戏用语，无特殊风险。",
        "source": "manual",
        "status": "published",
        "confidence": "medium",
        "view_count": 480,
        "vote_count": 15,
    },
    {
        "word": "塌房",
        "pinyin": "tā fáng",
        "meaning": "指偶像因负面事件导致形象崩塌、粉丝脱粉的现象。",
        "example": "他家偶像又塌房了，热搜第一。",
        "category": "饭圈用语",
        "risk_level": "medium",
        "risk_types": ["舆情", "名誉"],
        "risk_advice": "涉及个人名誉，引用真实人物时需谨慎。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 1620,
        "vote_count": 61,
    },
    {
        "word": "打call",
        "pinyin": "dǎ call",
        "meaning": "原指演唱会粉丝应援打call动作，现泛指公开表达支持与喜爱。",
        "example": "为这部新剧打call，强烈推荐！",
        "category": "饭圈用语",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "中性支持用语，无特殊风险。",
        "source": "database",
        "status": "published",
        "confidence": "high",
        "view_count": 890,
        "vote_count": 34,
    },
    {
        "word": "卷王",
        "pinyin": "juǎn wáng",
        "meaning": "指在竞争中最拼命、卷得最厉害的人，带调侃意味。",
        "example": "室友天天图书馆到半夜，真是卷王本王。",
        "category": "学术黑话",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "校园调侃用语，注意分寸。",
        "source": "ai",
        "status": "pending",
        "confidence": "medium",
        "view_count": 410,
        "vote_count": 12,
    },
    {
        "word": "割韭菜",
        "pinyin": "gē jiǔ cài",
        "meaning": "比喻利用信息差反复收割缺乏经验的投资者或消费者。",
        "example": "这币圈项目就是割韭菜，别上当。",
        "category": "金融投资",
        "risk_level": "high",
        "risk_types": ["金融", "舆情"],
        "risk_advice": "涉及金融风险，引用须提示投资有风险。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 1880,
        "vote_count": 70,
    },
    {
        "word": "三甲",
        "pinyin": "sān jiǎ",
        "meaning": "指三甲医院，即我国最高等级的医院，借指顶级医疗资源。",
        "example": "这病得去三甲看看，小医院查不出来。",
        "category": "医疗健康",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "医学术语，无特殊风险。",
        "source": "database",
        "status": "published",
        "confidence": "high",
        "view_count": 360,
        "vote_count": 9,
    },
    {
        "word": "知情权",
        "pinyin": "zhī qíng quán",
        "meaning": "消费者或当事人有权知晓与其利益相关真实信息的权利。",
        "example": "商家未标明成分，侵犯了消费者的知情权。",
        "category": "法律术语",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "规范法律术语，通用场景可用。",
        "source": "database",
        "status": "published",
        "confidence": "high",
        "view_count": 290,
        "vote_count": 7,
    },
    {
        "word": "大模型",
        "pinyin": "dà mó xíng",
        "meaning": "指参数规模巨大、具备强大通用能力的人工智能模型，如大语言模型。",
        "example": "现在各家都在卷大模型，应用场景越来越多。",
        "category": "科技数码",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "中性科技术语，无特殊风险。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 1050,
        "vote_count": 38,
    },
    {
        "word": "拼搭",
        "pinyin": "pīn dā",
        "meaning": "指把不同元素组合搭配的生活方式或玩法，如拼搭玩具、拼搭穿搭。",
        "example": "周末和孩子一起拼搭积木，很有成就感。",
        "category": "生活方式",
        "risk_level": "low",
        "risk_types": [],
        "risk_advice": "中性生活用语，无特殊风险。",
        "source": "manual",
        "status": "published",
        "confidence": "high",
        "view_count": 220,
        "vote_count": 6,
    },
    {
        "word": "拼图式社交",
        "pinyin": "pīn tú shì shè jiāo",
        "meaning": "指通过碎片化内容拼凑出自我形象、在社交平台展示人设的社交方式。",
        "example": "她的朋友圈就是典型的拼图式社交，每条都在立人设。",
        "category": "社交网络",
        "risk_level": "medium",
        "risk_types": ["舆情"],
        "risk_advice": "涉及社交心理，引用避免标签化评判他人。",
        "source": "ai",
        "status": "pending",
        "confidence": "medium",
        "view_count": 330,
        "vote_count": 11,
    },
]


# ---------------------------------------------------------------------------
# 初始化逻辑
# ---------------------------------------------------------------------------

def seed_categories(session) -> int:
    """插入一级分类，返回新增数量。"""
    added = 0
    for item in CATEGORIES:
        exists = session.scalar(select(Category).where(Category.name == item["name"]))
        if exists:
            continue
        session.add(
            Category(
                name=item["name"],
                icon=item["icon"],
                level=1,
                sort_order=item["sort_order"],
            )
        )
        added += 1
    session.commit()
    return added


def seed_users(session) -> int:
    """插入测试用户，返回新增数量。密码使用 bcrypt 哈希。"""
    added = 0
    for item in USERS:
        exists = session.scalar(select(User).where(User.username == item["username"]))
        if exists:
            continue
        session.add(
            User(
                username=item["username"],
                nickname=item["nickname"],
                password_hash=hash_password(item["password"]),
                level=item["level"],
                title=item.get("title"),
                experience=item.get("experience", 0),
            )
        )
        added += 1
    session.commit()
    return added


def seed_achievements(session) -> int:
    """插入成就配置，返回新增数量。"""
    added = 0
    for item in ACHIEVEMENTS:
        exists = session.scalar(
            select(Achievement).where(Achievement.name == item["name"])
        )
        if exists:
            continue
        session.add(
            Achievement(
                name=item["name"],
                description=item["description"],
                type=item["type"],
                icon=item.get("icon"),
                condition=item["condition"],
                experience_reward=item["experience_reward"],
            )
        )
        added += 1
    session.commit()
    return added


def seed_words(session, admin_user_id: int) -> int:
    """插入示例词条，返回新增数量。"""
    added = 0
    for item in WORDS:
        exists = session.scalar(select(Word).where(Word.word == item["word"]))
        if exists:
            continue
        category = session.scalar(
            select(Category).where(Category.name == item["category"])
        )
        if category is None:
            print(f"  [跳过] 未找到分类：{item['category']}（词条：{item['word']}）")
            continue
        session.add(
            Word(
                word=item["word"],
                pinyin=item.get("pinyin"),
                meaning=item["meaning"],
                example=item.get("example"),
                category_id=category.id,
                risk_level=item["risk_level"],
                risk_types=item.get("risk_types"),
                risk_advice=item.get("risk_advice"),
                source=item["source"],
                status=item["status"],
                confidence=item.get("confidence"),
                view_count=item.get("view_count", 0),
                vote_count=item.get("vote_count", 0),
                created_by=admin_user_id,
            )
        )
        added += 1
    session.commit()
    return added


def main() -> None:
    print("=" * 60)
    print("黑话翻译系统 - 初始化数据脚本")
    print("=" * 60)

    # 1. 创建所有表
    print("[1/5] 创建数据库表 ...")
    init_db()
    print("      表结构创建完成。")

    with SessionLocal() as session:
        # 2. 分类
        print("[2/5] 插入一级分类 ...")
        cat_added = seed_categories(session)
        print(f"      新增分类 {cat_added} 个（共 {len(CATEGORIES)} 个）。")

        # 3. 用户
        print("[3/5] 插入测试用户 ...")
        user_added = seed_users(session)
        print(f"      新增用户 {user_added} 个（共 {len(USERS)} 个）。")

        # 4. 成就
        print("[4/5] 插入成就配置 ...")
        ach_added = seed_achievements(session)
        print(f"      新增成就 {ach_added} 个（共 {len(ACHIEVEMENTS)} 个）。")

        # 5. 词条
        print("[5/5] 插入示例词条 ...")
        admin = session.scalar(select(User).where(User.username == "admin"))
        admin_id = admin.id if admin else None
        word_added = seed_words(session, admin_user_id=admin_id)
        print(f"      新增词条 {word_added} 个（共 {len(WORDS)} 个）。")

    print("=" * 60)
    print("初始化完成。可使用 uvicorn main:app --reload 启动服务。")
    print("=" * 60)


if __name__ == "__main__":
    main()
