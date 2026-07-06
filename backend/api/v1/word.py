"""词条接口

对应 SDD 4.5.4：
- GET /words：词条列表（分页、分类筛选、排序）
- GET /words/search：搜索词条
- GET /words/{word_id}：词条详情
- POST /words/{word_id}/favorite：收藏词条
- DELETE /words/{word_id}/favorite：取消收藏
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_current_user_required
from core.database import get_db
from models.category import Category
from models.user import Favorite, User
from models.word import Word
from schemas import BaseResponse
from services.word_service import WordService

router = APIRouter(prefix="/words", tags=["词条"])

# 排序字段映射
SORT_MAP = {
    "hot": Word.view_count.desc(),
    "new": Word.created_at.desc(),
    "name": Word.word.asc(),
}


@router.get("", response_model=BaseResponse)
async def list_words(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: int | None = Query(None, description="按分类筛选"),
    tag: str | None = Query(None, description="按标签筛选"),
    sort: str = Query("hot", description="排序：hot/new/name"),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """词条列表（分页、分类筛选、排序）。"""
    if sort not in SORT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort 取值非法，仅支持 hot/new/name",
        )

    query = select(Word).where(
        Word.status == "published",
        Word.deleted_at.is_(None),
    )
    if category_id is not None:
        query = query.where(Word.category_id == category_id)

    # 总数
    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()

    # 分页
    query = query.order_by(SORT_MAP[sort]).offset((page - 1) * page_size).limit(page_size)
    words = db.execute(query).scalars().all()

    # 批量查询分类与收藏数
    category_ids = {w.category_id for w in words if w.category_id}
    categories = {
        c.id: c
        for c in db.execute(
            select(Category).where(Category.id.in_(category_ids))
        ).scalars().all()
    } if category_ids else {}

    word_ids = [w.id for w in words]
    fav_counts = {}
    if word_ids:
        rows = db.execute(
            select(Favorite.word_id, func.count(Favorite.id))
            .where(Favorite.word_id.in_(word_ids))
            .group_by(Favorite.word_id)
        ).all()
        fav_counts = {row[0]: row[1] for row in rows}

    items = [
        {
            "id": w.id,
            "word": w.word,
            "pinyin": w.pinyin,
            "summary": w.meaning,
            "category": (
                categories[w.category_id].name
                if w.category_id and w.category_id in categories
                else None
            ),
            "tags": w.risk_types or [],
            "view_count": w.view_count,
            "favorite_count": fav_counts.get(w.id, 0),
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in words
    ]

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/search", response_model=BaseResponse)
async def search_words(
    keyword: str = Query(..., min_length=1, max_length=50, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """搜索词条。"""
    service = WordService()
    results = service.search(keyword, db)

    # 分页
    total = len(results)
    start = (page - 1) * page_size
    paged = results[start: start + page_size]

    items = [
        {
            "id": r.get("id"),
            "word": r.get("word", ""),
            "summary": r.get("meaning", ""),
            "highlight": f"<em>{keyword}</em>" if keyword in r.get("word", "") else r.get("word", ""),
            "match_score": 0.98 if r.get("word") == keyword else 0.85,
        }
        for r in paged
    ]

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{word_id}", response_model=BaseResponse)
async def get_word_detail(
    word_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> BaseResponse:
    """词条详情（含多语境、别名、相关词条）。

    认证可选：已登录用户可额外获取 is_favorited 字段。
    """
    service = WordService()
    detail = service.get_detail(word_id, db)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="词条不存在",
        )

    # 浏览数 +1
    word = db.get(Word, word_id)
    if word is not None:
        word.view_count = (word.view_count or 0) + 1
        db.commit()

    # 查询当前用户是否已收藏
    is_favorited = False
    if user is not None:
        fav = db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id,
                Favorite.word_id == word_id,
            )
        ).scalar_one_or_none()
        is_favorited = fav is not None

    # 收藏总数
    favorite_count = db.execute(
        select(func.count(Favorite.id)).where(Favorite.word_id == word_id)
    ).scalar_one()

    detail["is_favorited"] = is_favorited
    detail["favorite_count"] = favorite_count
    detail["definition"] = detail.pop("meaning", "")
    detail["tags"] = detail.get("risk_types") or []
    detail["updated_at"] = detail.get("created_at")
    return BaseResponse(data=detail)


@router.post("/{word_id}/favorite", response_model=BaseResponse)
async def favorite_word(
    word_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """收藏词条。"""
    word = db.get(Word, word_id)
    if word is None or word.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="词条不存在",
        )

    existing = db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.word_id == word_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已收藏该词条",
        )

    db.add(Favorite(user_id=user.id, word_id=word_id))
    db.commit()

    favorite_count = db.execute(
        select(func.count(Favorite.id)).where(Favorite.word_id == word_id)
    ).scalar_one()

    return BaseResponse(data={
        "word_id": word_id,
        "is_favorited": True,
        "favorite_count": favorite_count,
    })


@router.delete("/{word_id}/favorite", response_model=BaseResponse)
async def unfavorite_word(
    word_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> BaseResponse:
    """取消收藏。"""
    fav = db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.word_id == word_id,
        )
    ).scalar_one_or_none()
    if fav is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏记录不存在",
        )

    db.delete(fav)
    db.commit()

    favorite_count = db.execute(
        select(func.count(Favorite.id)).where(Favorite.word_id == word_id)
    ).scalar_one()

    return BaseResponse(data={
        "word_id": word_id,
        "is_favorited": False,
        "favorite_count": favorite_count,
    })
