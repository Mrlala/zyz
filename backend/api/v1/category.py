"""分类接口

对应 SDD 4.5.5：
- GET /categories：分类树
- GET /categories/{category_id}/words：分类下词条
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from models.category import Category
from models.word import Word
from schemas import BaseResponse

router = APIRouter(prefix="/categories", tags=["分类"])

# 排序字段映射
SORT_MAP = {
    "hot": Word.view_count.desc(),
    "new": Word.created_at.desc(),
    "name": Word.word.asc(),
}


@router.get("", response_model=BaseResponse)
async def get_category_tree(
    db: Session = Depends(get_db),
) -> BaseResponse:
    """获取分类树（支持自引用三级层级）。"""
    categories = (
        db.execute(
            select(Category).order_by(Category.level, Category.sort_order)
        )
        .scalars()
        .all()
    )

    # 统计每个分类下的词条数
    word_counts = {}
    count_rows = db.execute(
        select(Word.category_id, func.count(Word.id))
        .where(Word.status == "published", Word.deleted_at.is_(None))
        .group_by(Word.category_id)
    ).all()
    word_counts = {row[0]: row[1] for row in count_rows}

    # 构建分类树
    cat_map: dict[int, dict] = {}
    for c in categories:
        cat_map[c.id] = {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "word_count": word_counts.get(c.id, 0),
            "children": [],
        }

    tree: list[dict] = []
    for c in categories:
        node = cat_map[c.id]
        if c.parent_id is None:
            tree.append(node)
        elif c.parent_id in cat_map:
            # 子分类仅保留 id/name/icon/word_count
            cat_map[c.parent_id]["children"].append(node)

    return BaseResponse(data=tree)


@router.get("/{category_id}/words", response_model=BaseResponse)
async def get_category_words(
    category_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query("hot", description="排序：hot/new/name"),
    db: Session = Depends(get_db),
) -> BaseResponse:
    """获取分类下词条列表。"""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在",
        )

    if sort not in SORT_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort 取值非法",
        )

    query = select(Word).where(
        Word.category_id == category_id,
        Word.status == "published",
        Word.deleted_at.is_(None),
    )
    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()

    query = query.order_by(SORT_MAP[sort]).offset((page - 1) * page_size).limit(page_size)
    words = db.execute(query).scalars().all()

    items = [
        {
            "id": w.id,
            "word": w.word,
            "summary": w.meaning,
            "pinyin": w.pinyin,
            "view_count": w.view_count,
            "vote_count": w.vote_count,
        }
        for w in words
    ]

    return BaseResponse(data={
        "category": {"id": category.id, "name": category.name},
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
