"""工作台接口（后台）

- GET /dashboard/overview：数据概览

权限：已登录管理员即可（get_admin_required）
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import get_admin_required
from models.admin import AdminAccount, AdminAccount as Admin
from models.feedback import Feedback
from models.submission import CorrectionReport, Submission
from models.translation import Translation
from models.user import User
from models.word import Word
from schemas import BaseResponse

router = APIRouter(prefix="/dashboard", tags=["工作台"])


@router.get("/overview", response_model=BaseResponse)
async def overview(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(get_admin_required),
) -> BaseResponse:
    """数据概览。

    返回：词条总数、用户总数、今日翻译数、待审核提交数、待审核纠错数、管理员数、
    近 7 天翻译趋势、热词 Top10。
    """
    # 词条总数（软删除排除）
    word_count = db.execute(
        select(func.count(Word.id)).where(Word.deleted_at.is_(None))
    ).scalar_one()

    # 用户总数
    user_count = db.execute(select(func.count(User.id))).scalar_one()

    # 今日翻译数
    translation_count_today = db.execute(
        select(func.count(Translation.id)).where(
            func.date(Translation.created_at) == func.current_date()
        )
    ).scalar_one()

    # 待审核提交数
    submission_pending = db.execute(
        select(func.count(Submission.id)).where(Submission.status == "pending")
    ).scalar_one()

    # 待审核纠错数
    correction_pending = db.execute(
        select(func.count(CorrectionReport.id)).where(CorrectionReport.status == "pending")
    ).scalar_one()

    # 管理员数
    admin_count = db.execute(select(func.count(AdminAccount.id))).scalar_one()

    # 近 7 天翻译趋势
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    daily_rows = db.execute(
        select(
            func.date(Translation.created_at).label("date"),
            func.count(Translation.id).label("count"),
        )
        .where(Translation.created_at >= start)
        .group_by(func.date(Translation.created_at))
        .order_by(func.date(Translation.created_at))
    ).all()
    translation_trend = [{"date": str(row.date), "count": row.count} for row in daily_rows]

    # 热词 Top10：按 view_count 倒序，限定已发布且未删除
    hot_words = (
        db.execute(
            select(Word)
            .where(Word.status == "published", Word.deleted_at.is_(None))
            .order_by(Word.view_count.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    hot_top10 = [
        {"id": w.id, "word": w.word, "heat": w.view_count or 0}
        for w in hot_words
    ]

    return BaseResponse(data={
        "word_count": word_count,
        "user_count": user_count,
        "translation_count_today": translation_count_today,
        "submission_pending": submission_pending,
        "correction_pending": correction_pending,
        "admin_count": admin_count,
        "translation_trend": translation_trend,
        "hot_top10": hot_top10,
    })
