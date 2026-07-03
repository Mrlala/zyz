"""后台管理初始化数据脚本

用法（在 backend/ 目录下执行）：
    python -m data.init_admin_data

功能：
    1. 初始化 3 个内置角色（sys_admin / sec_admin / auditor）
    2. 初始化 13 个权限点
    3. 初始化角色-权限关联（按 plan-admin-system.md 矩阵）
    4. 初始化默认 sys_admin 账号（admin / admin123，首次登录强制改密）
    5. 初始化 AI 配置默认项（从 .env 兜底）

脚本幂等，可重复执行：已存在的记录会被跳过。
对应 plan-admin-system.md 阶段 A 步骤 3。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保以 `python -m data.init_admin_data` 或直接运行脚本均可正确导入 backend 顶层模块
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy import select  # noqa: E402

from config import settings  # noqa: E402
from core.database import SessionLocal, init_db  # noqa: E402
from core.security import hash_password  # noqa: E402
from models.admin import (  # noqa: E402
    AdminAccount,
    Permission,
    Role,
    RolePermission,
    SystemConfig,
)


# ---------------------------------------------------------------------------
# 角色定义
# ---------------------------------------------------------------------------

ROLES: list[dict] = [
    {"code": "sys_admin", "name": "系统管理员", "description": "账号管理、系统配置、词库运维、AI 密钥", "is_builtin": True},
    {"code": "sec_admin", "name": "安全保密管理员", "description": "角色权限分配、安全策略、风险等级终审", "is_builtin": True},
    {"code": "auditor", "name": "安全审计管理员", "description": "只读：操作日志、登录日志、API 调用审计", "is_builtin": True},
]


# ---------------------------------------------------------------------------
# 权限点定义
# ---------------------------------------------------------------------------

PERMISSIONS: list[dict] = [
    {"code": "system:user:manage", "name": "账号管理", "module": "system"},
    {"code": "system:role:manage", "name": "角色权限配置", "module": "system"},
    {"code": "system:config:manage", "name": "系统配置", "module": "system"},
    {"code": "content:word:manage", "name": "词库增删改", "module": "content"},
    {"code": "content:word:audit", "name": "词条状态审核", "module": "content"},
    {"code": "content:submission:audit", "name": "用户提交审核", "module": "content"},
    {"code": "content:correction:audit", "name": "纠错审核", "module": "content"},
    {"code": "content:category:manage", "name": "分类管理", "module": "content"},
    {"code": "ai:config:manage", "name": "AI 配置管理", "module": "ai"},
    {"code": "monitor:api:view", "name": "API 用量监控查看", "module": "monitor"},
    {"code": "monitor:ai:view", "name": "AI 调用明细查看", "module": "monitor"},
    {"code": "audit:log:view", "name": "操作日志查看", "module": "audit"},
    {"code": "audit:log:export", "name": "日志导出", "module": "audit"},
]


# ---------------------------------------------------------------------------
# 角色-权限矩阵（permission code 列表）
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "sys_admin": [
        "system:user:manage",
        "system:config:manage",
        "content:word:manage",
        "content:word:audit",
        "content:submission:audit",
        "content:correction:audit",
        "content:category:manage",
        "ai:config:manage",
        "monitor:api:view",
        "monitor:ai:view",
    ],
    "sec_admin": [
        "system:role:manage",
        "system:config:manage",
        "content:word:audit",
        "ai:config:manage",
    ],
    "auditor": [
        "monitor:api:view",
        "monitor:ai:view",
        "audit:log:view",
        "audit:log:export",
    ],
}


# ---------------------------------------------------------------------------
# AI 配置默认项（从 .env 兜底）
# ---------------------------------------------------------------------------

AI_CONFIGS: list[dict] = [
    {
        "config_key": "deepseek_api_key",
        "config_value": settings.DEEPSEEK_API_KEY,
        "value_type": "string",
        "category": "ai",
        "description": "DeepSeek API 密钥",
        "is_sensitive": True,
    },
    {
        "config_key": "deepseek_api_url",
        "config_value": settings.DEEPSEEK_API_URL,
        "value_type": "string",
        "category": "ai",
        "description": "DeepSeek API 地址",
        "is_sensitive": False,
    },
    {
        "config_key": "deepseek_model",
        "config_value": settings.DEEPSEEK_MODEL,
        "value_type": "string",
        "category": "ai",
        "description": "DeepSeek 模型名称",
        "is_sensitive": False,
    },
    {
        "config_key": "deepseek_temperature",
        "config_value": "0.3",
        "value_type": "float",
        "category": "ai",
        "description": "生成温度（0-2）",
        "is_sensitive": False,
    },
    {
        "config_key": "deepseek_max_tokens",
        "config_value": "2048",
        "value_type": "int",
        "category": "ai",
        "description": "单次最大输出 token 数",
        "is_sensitive": False,
    },
    {
        "config_key": "translate_system_prompt",
        "config_value": None,  # 首次初始化时填入默认 Prompt 全文
        "value_type": "text",
        "category": "ai",
        "description": "翻译系统提示词（System Prompt）",
        "is_sensitive": False,
    },
]


# ---------------------------------------------------------------------------
# 初始化逻辑
# ---------------------------------------------------------------------------

def init_admin_data() -> None:
    """初始化后台管理种子数据（幂等）。"""
    init_db()
    db = SessionLocal()
    try:
        # 1. 角色
        role_map: dict[str, Role] = {}
        for r in ROLES:
            existing = db.execute(select(Role).where(Role.code == r["code"])).scalar_one_or_none()
            if existing is None:
                role = Role(**r)
                db.add(role)
                db.flush()
                role_map[r["code"]] = role
                print(f"[角色] 创建 {r['code']} ({r['name']})")
            else:
                role_map[r["code"]] = existing
                print(f"[角色] 已存在 {r['code']}")

        # 2. 权限点
        perm_map: dict[str, Permission] = {}
        for p in PERMISSIONS:
            existing = db.execute(select(Permission).where(Permission.code == p["code"])).scalar_one_or_none()
            if existing is None:
                perm = Permission(**p)
                db.add(perm)
                db.flush()
                perm_map[p["code"]] = perm
                print(f"[权限] 创建 {p['code']}")
            else:
                perm_map[p["code"]] = existing

        # 3. 角色-权限关联
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = role_map.get(role_code)
            if role is None:
                continue
            for perm_code in perm_codes:
                perm = perm_map.get(perm_code)
                if perm is None:
                    continue
                exists = db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                ).scalar_one_or_none()
                if exists is None:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        db.flush()
        print(f"[角色权限] 关联已建立（{sum(len(v) for v in ROLE_PERMISSIONS.values())} 条）")

        # 4. 默认 sys_admin 账号
        admin = db.execute(select(AdminAccount).where(AdminAccount.username == "admin")).scalar_one_or_none()
        if admin is None:
            sys_role = role_map.get("sys_admin")
            admin = AdminAccount(
                username="admin",
                password_hash=hash_password("admin123"),
                nickname="超级管理员",
                role_id=sys_role.id,
                status="active",
                must_change_password=True,
                created_by=None,
            )
            db.add(admin)
            print("[账号] 创建默认管理员 admin / admin123（首次登录需改密）")
        else:
            print("[账号] 管理员 admin 已存在")

        # 5. AI 配置默认项
        for cfg in AI_CONFIGS:
            existing = db.execute(
                select(SystemConfig).where(SystemConfig.config_key == cfg["config_key"])
            ).scalar_one_or_none()
            if existing is None:
                # translate_system_prompt 首次初始化时填入默认 Prompt 全文
                if cfg["config_key"] == "translate_system_prompt" and not cfg.get("config_value"):
                    from services.ai.prompts import DEFAULT_SYSTEM_PROMPT
                    cfg["config_value"] = DEFAULT_SYSTEM_PROMPT
                db.add(SystemConfig(**cfg))
                print(f"[配置] 创建 {cfg['config_key']}")
            else:
                print(f"[配置] 已存在 {cfg['config_key']}")

        db.commit()
        print("\n后台管理初始化数据写入完成。")
    finally:
        db.close()


if __name__ == "__main__":
    init_admin_data()
