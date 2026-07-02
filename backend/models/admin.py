"""后台管理数据模型

定义后台管理系统所需的表：
- AdminAccount：管理员账号（独立于 C 端 users 表）
- Role：角色定义（sys_admin / sec_admin / auditor）
- Permission：权限点字典
- RolePermission：角色-权限关联
- OperationLog：操作审计日志（只增不删）
- AiCallLog：AI 调用明细（token 消耗/成本/耗时）
- SystemConfig：系统配置 KV 表（支持在线修改 AI 配置等）

对应 plan-admin-system.md 第四章数据库改造。
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from models.base import Base, BaseModel, CreatedAtMixin


class AdminAccount(BaseModel):
    """管理员账号表（独立于 C 端 users 表）。

    管理员使用账号密码登录，与 C 端 device_id 登录体系分离。
    """

    __tablename__ = "admin_accounts"
    __table_args__ = (UniqueConstraint("username", name="uq_admin_username"),)

    username = Column(String(50), nullable=False, comment="登录用户名")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 密码哈希")
    nickname = Column(String(50), nullable=True, comment="显示昵称")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="角色 ID")
    status = Column(String(20), nullable=False, default="active", comment="状态：active/disabled")
    last_login_at = Column(String(30), nullable=True, comment="最近登录时间 ISO")
    last_login_ip = Column(String(45), nullable=True, comment="最近登录 IP")
    must_change_password = Column(Boolean, nullable=False, default=False, comment="是否需强制改密")
    failed_login_count = Column(Integer, nullable=False, default=0, comment="连续登录失败次数")
    locked_until = Column(DateTime, nullable=True, comment="锁定截止时间，NULL 表示未锁定")
    created_by = Column(Integer, nullable=True, comment="创建者 admin_id")

    role = relationship("Role", lazy="joined")


class Role(BaseModel):
    """角色定义表。

    内置三员：sys_admin / sec_admin / auditor，is_builtin=True 不可删除。
    """

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_role_code"),)

    code = Column(String(50), nullable=False, comment="角色代码")
    name = Column(String(50), nullable=False, comment="角色名称")
    description = Column(String(200), nullable=True, comment="角色描述")
    is_builtin = Column(Boolean, nullable=False, default=False, comment="是否内置角色（不可删）")

    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(BaseModel):
    """权限点字典表。

    按 module 分组，code 全局唯一，格式如 system:user:manage。
    """

    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("code", name="uq_permission_code"),)

    code = Column(String(80), nullable=False, comment="权限代码，如 system:user:manage")
    name = Column(String(50), nullable=False, comment="权限名称")
    module = Column(String(30), nullable=False, comment="所属模块，如 system/content/ai/monitor/audit")


class RolePermission(BaseModel):
    """角色-权限关联表（多对多）。"""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", lazy="joined")


class OperationLog(Base, CreatedAtMixin):
    """操作审计日志表（只增不删）。

    记录所有 /api/manage/* 请求，供安全审计管理员查询。
    """

    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=True, comment="操作者 admin_id（登录接口可能为空）")
    username = Column(String(50), nullable=True, comment="操作者用户名（冗余便于查询）")
    module = Column(String(30), nullable=True, comment="业务模块，如 account/word/ai_config")
    action = Column(String(30), nullable=True, comment="动作，如 login/create/update/delete")
    method = Column(String(10), nullable=False, comment="HTTP 方法")
    path = Column(String(200), nullable=False, comment="请求路径")
    params = Column(Text, nullable=True, comment="请求参数 JSON（脱敏后）")
    ip = Column(String(45), nullable=True, comment="客户端 IP")
    user_agent = Column(String(255), nullable=True, comment="User-Agent")
    status_code = Column(Integer, nullable=False, comment="响应状态码")
    duration_ms = Column(Integer, nullable=False, default=0, comment="耗时毫秒")
    error_msg = Column(String(500), nullable=True, comment="错误信息（如有）")


class AiCallLog(Base, CreatedAtMixin):
    """AI 调用明细日志表。

    记录每次 DeepSeek 调用的 token 消耗、耗时、成本与成功/降级状态。
    """

    __tablename__ = "ai_call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=True, comment="触发调用的 admin_id（可空）")
    user_id = Column(Integer, nullable=True, comment="触发调用的 C 端 user_id（可空）")
    endpoint = Column(String(100), nullable=False, comment="调用入口，如 translate/ai-config-test")
    mode = Column(String(20), nullable=True, comment="翻译模式 translate/dict")
    prompt_tokens = Column(Integer, nullable=True, default=0, comment="输入 token 数")
    completion_tokens = Column(Integer, nullable=True, default=0, comment="输出 token 数")
    total_tokens = Column(Integer, nullable=True, default=0, comment="总 token 数")
    duration_ms = Column(Integer, nullable=False, default=0, comment="耗时毫秒")
    success = Column(Boolean, nullable=False, default=True, comment="是否成功")
    fallback_used = Column(Boolean, nullable=False, default=False, comment="是否降级到词库模式")
    error_msg = Column(String(500), nullable=True, comment="错误信息")
    cost_estimate = Column(String(20), nullable=True, comment="成本估算（元）")


class SystemConfig(BaseModel):
    """系统配置 KV 表。

    支持在线修改的配置项，如 AI 密钥/模型/参数、系统设置等。
    前端管理后台修改后，后端服务带内存缓存读取。
    """

    __tablename__ = "system_configs"
    __table_args__ = (UniqueConstraint("config_key", name="uq_config_key"),)

    config_key = Column(String(80), nullable=False, comment="配置键，如 deepseek_api_key")
    config_value = Column(Text, nullable=True, comment="配置值")
    value_type = Column(String(20), nullable=False, default="string", comment="值类型：string/int/float/bool/json")
    category = Column(String(30), nullable=False, default="general", comment="分类：ai/system/content")
    description = Column(String(200), nullable=True, comment="配置说明")
    is_sensitive = Column(Boolean, nullable=False, default=False, comment="是否敏感（前端脱敏展示）")
