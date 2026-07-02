"""全局搜索接口

- GET /manage/search?q={keyword}&limit=5：跨模块聚合搜索
  按当前管理员权限过滤结果，返回分组数据：
  { words: [...], submissions: [...], admins: [...], logs: [...] }
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import get_admin_permissions, get_admin_required
from models.admin import AdminAccount, OperationLog
from models.submission import Submission
from models.word import Word
from schemas import BaseResponse

router = APIRouter(prefix="/search", tags=["全局搜索"])


@router.get("", response_model=BaseResponse)
async def global_search(
    q: str = Query(..., min_length=1, max_length=50, description="搜索关键词"),
    limit: int = Query(5, ge=1, le=20, description="每组返回条数上限"),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(get_admin_required),
) -> BaseResponse:
    """跨模块聚合搜索

    按当前管理员权限过滤结果：
    - 词条：需 content:word:manage
    - 用户提交：需 content:submission:audit
    - 管理员：需 system:user:manage
    - 操作日志：需 audit:log:view
    """
    keyword = f"%{q}%"
    perms = get_admin_permissions(db, admin)  # set[str]
    result: dict = {"words": [], "submissions": [], "admins": [], "logs": []}

    # 词条搜索
    if "content:word:manage" in perms:
        words = db.execute(
            select(Word)
            .where(
                Word.deleted_at.is_(None),
                or_(Word.word.like(keyword), Word.pinyin.like(keyword), Word.meaning.like(keyword)),
            )
            .order_by(Word.view_count.desc())
            .limit(limit)
        ).scalars().all()
        result["words"] = [
            {
                "id": w.id,
                "word": w.word,
                "pinyin": w.pinyin,
                "meaning": (w.meaning or "")[:80],
                "status": w.status,
                "view_count": w.view_count,
            }
            for w in words
        ]

    # 用户提交搜索
    if "content:submission:audit" in perms:
        subs = db.execute(
            select(Submission)
            .where(or_(Submission.word.like(keyword), Submission.meaning.like(keyword)))
            .order_by(Submission.created_at.desc())
            .limit(limit)
        ).scalars().all()
        result["submissions"] = [
            {
                "id": s.id,
                "word": s.word,
                "meaning": (s.meaning or "")[:80],
                "status": s.status,
                "user_id": s.user_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ]

    # 管理员搜索
    if "system:user:manage" in perms:
        admins = db.execute(
            select(AdminAccount)
            .where(or_(AdminAccount.username.like(keyword), AdminAccount.nickname.like(keyword)))
            .limit(limit)
        ).scalars().all()
        result["admins"] = [
            {
                "id": a.id,
                "username": a.username,
                "nickname": a.nickname or "",
                "status": a.status,
            }
            for a in admins
        ]

    # 操作日志搜索（按 module/action/path 关键词）
    if "audit:log:view" in perms:
        logs = db.execute(
            select(OperationLog)
            .where(
                or_(
                    OperationLog.module.like(keyword),
                    OperationLog.action.like(keyword),
                    OperationLog.path.like(keyword),
                    OperationLog.username.like(keyword),
                )
            )
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
        ).scalars().all()
        result["logs"] = [
            {
                "id": log.id,
                "username": log.username or "",
                "module": log.module,
                "action": log.action,
                "method": log.method,
                "path": log.path,
                "status_code": log.status_code,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    return BaseResponse(code=0, message="success", data=result)
