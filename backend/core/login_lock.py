"""登录失败锁定模块

对连续登录失败的账号进行临时锁定，防止暴力破解。
- 达到 MAX_FAILED_ATTEMPTS 次后锁定 LOCK_DURATION_MINUTES 分钟
- 锁定期间拒绝登录，返回 423 Locked
- 锁定过期后自动解锁（失败计数归零）

适用于管理员账号和 C 端账号密码登录。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

# 锁定策略
MAX_FAILED_ATTEMPTS = 5  # 连续失败 5 次后锁定
LOCK_DURATION_MINUTES = 15  # 锁定 15 分钟


def is_locked(locked_until: datetime | None) -> bool:
    """检查账号是否处于锁定状态。

    :param locked_until: 账号的锁定截止时间，None 表示未锁定
    :return: True 表示当前处于锁定中
    """
    if locked_until is None:
        return False
    # locked_until 可能是 ISO 字符串（AdminAccount.last_login_at 风格）或 datetime
    if isinstance(locked_until, str):
        try:
            locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
        except ValueError:
            return False
    now = datetime.now(timezone.utc)
    # 确保 locked_until 是 timezone-aware
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return now < locked_until


def get_remaining_lock_seconds(locked_until: datetime | None) -> int:
    """获取锁定剩余秒数（用于返回给前端提示）。"""
    if locked_until is None:
        return 0
    if isinstance(locked_until, str):
        try:
            locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
        except ValueError:
            return 0
    now = datetime.now(timezone.utc)
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    remaining = (locked_until - now).total_seconds()
    return max(0, int(remaining))


def compute_lock_until() -> datetime:
    """计算锁定截止时间（当前时间 + 锁定时长）。"""
    return datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)


def should_lock(failed_count: int) -> bool:
    """判断失败次数是否达到锁定阈值。"""
    return failed_count >= MAX_FAILED_ATTEMPTS


def lock_message(locked_until: datetime | None) -> str:
    """生成锁定提示消息。"""
    remaining = get_remaining_lock_seconds(locked_until)
    if remaining > 60:
        minutes = remaining // 60
        return f"账号已锁定，请 {minutes} 分钟后重试"
    return f"账号已锁定，请 {remaining} 秒后重试"
