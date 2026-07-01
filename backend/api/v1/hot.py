"""热词接口

对应 SDD 4.5.7：
- GET /hot/daily：每日热词
- POST /hot/{word_id}/vote：热词投票
- GET /hot/ranking：热词排行榜
- GET /hot/history：学习历史
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_current_user_required
from core.database import get_db
from models.user import LearnRecord, User
from models.word import Word
from schemas import BaseResponse
from services.hotword_service import HotWordService

router = APIRouter(prefix="/hot", tags=["热词"])


@router.get("/daily", response_model=BaseResponse)
async def get_daily_hot(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> BaseResponse:
    """获取每日热词（固定 10 条）。"""
    service = HotWordService()
    user_id = user.id if user else None
    items = service.get_daily(user_id, db)

    daily_list = [
        {
            "rank": idx + 1,
            "id": item.get("word_id"),
            "word": item.get("word", ""),
            "heat": item.get("hot_score", 0),
            "vote_count": item.get("vote_count", 0),
        }
        for idx, item in enumerate(items)
    ]

    return BaseResponse(data={
        "date": date.today().isoformat(),
        "list": daily_list,
    })


@router.post("/{word_id}/vote", response_model=BaseResponse)
async def vote_word(
    word_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """对热词投票（默认 upvote）。"""
    service = HotWordService()
    try:
        result = service.vote(user.id, word_id, "upvote", db)
    except ValueError as exc:
        msg = str(exc)
        if "不存在" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "已" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return BaseResponse(data={
        "word_id": word_id,
        "vote_count": result.get("vote_count", 0),
        "has_voted": True,
    })


@router.get("/ranking", response_model=BaseResponse)
async def get_ranking(
    period: str = Query("daily", description="周期：daily/weekly/monthly"),
    limit: int = Query(50, ge=1, le=100, description="返回条数"),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """获取热词排行榜。"""
    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period 取值非法，仅支持 daily/weekly/monthly",
        )

    service = HotWordService()
    # 将 period 透传给 service，按时间窗口统计真实热度
    items = service.get_ranking(db, limit=limit, period=period)

    ranking_list = [
        {
            "rank": idx + 1,
            "id": item.get("word_id"),
            "word": item.get("word", ""),
            # heat 优先取 service 注入的窗口内翻译次数，回退到 hot_score
            "heat": item.get("heat", item.get("hot_score", 0)),
            "vote_count": item.get("vote_count", 0),
        }
        for idx, item in enumerate(items)
    ]

    return BaseResponse(data={
        "period": period,
        "list": ranking_list,
    })


@router.get("/history", response_model=BaseResponse)
async def get_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """获取用户学习历史。"""
    # 总数
    total = db.execute(
        select(func.count(LearnRecord.id)).where(LearnRecord.user_id == user.id)
    ).scalar_one()

    # 分页查询
    offset = (page - 1) * page_size
    rows = (
        db.execute(
            select(LearnRecord, Word)
            .join(Word, LearnRecord.word_id == Word.id)
            .where(LearnRecord.user_id == user.id)
            .order_by(LearnRecord.learned_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        .all()
    )

    items = [
        {
            "word_id": record.word_id,
            "word": word.word,
            "action": record.status,
            "happened_at": record.learned_at.isoformat() if record.learned_at else None,
        }
        for record, word in rows
    ]

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
