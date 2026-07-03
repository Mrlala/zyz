"""词库管理接口（后台）

- GET    /manage/words：词条列表（分页/筛选状态/风险/关键词）
- POST   /manage/words：创建词条
- GET    /manage/words/{id}：词条详情
- PUT    /manage/words/{id}：更新词条
- DELETE /manage/words/{id}：删除词条（软删除）
- PUT    /manage/words/{id}/status：审核状态变更（发布/下架/拒绝）
- PUT    /manage/words/{id}/risk：标记风险

权限：content:word:manage（CRUD）、content:word:audit（状态审核）
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount
from models.category import Category
from models.word import Word
from schemas import BaseResponse
from services.word_service import WordService

router = APIRouter(prefix="/words", tags=["词库管理"])


class WordCreateRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    pinyin: str | None = None
    meaning: str = Field(..., min_length=1)
    example: str | None = None
    origin: str | None = None
    category_id: int = Field(..., gt=0)
    risk_level: str = Field("low", description="low/medium/high")


class WordUpdateRequest(BaseModel):
    word: str | None = None
    pinyin: str | None = None
    meaning: str | None = None
    example: str | None = None
    origin: str | None = None
    category_id: int | None = None


class WordStatusRequest(BaseModel):
    status: str = Field(..., description="published/approved/rejected/pending")


class WordRiskRequest(BaseModel):
    risk_level: str = Field(..., description="low/medium/high")
    risk_types: list[str] = Field(default_factory=list)
    advice: str = ""


class BatchStatusRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)
    status: str = Field(..., description="published/approved/rejected/pending")


class BatchDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)


@router.get("", response_model=BaseResponse)
async def list_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    risk_level: str | None = Query(None),
    category_id: int | None = Query(None),
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """词库管理列表。"""
    query = select(Word).where(Word.deleted_at.is_(None))
    if keyword:
        query = query.where(Word.word.like(f"%{keyword}%"))
    if status_filter:
        query = query.where(Word.status == status_filter)
    if risk_level:
        query = query.where(Word.risk_level == risk_level)
    if category_id:
        query = query.where(Word.category_id == category_id)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    query = query.order_by(Word.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    words = db.execute(query).scalars().all()

    items = [
        {
            "id": w.id,
            "word": w.word,
            "pinyin": w.pinyin,
            "meaning": (w.meaning[:80] + "...") if w.meaning and len(w.meaning) > 80 else w.meaning,
            "category_id": w.category_id,
            "status": w.status,
            "risk_level": w.risk_level,
            "view_count": w.view_count,
            "vote_count": w.vote_count,
            "source": w.source,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in words
    ]
    return BaseResponse(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.post("", response_model=BaseResponse)
async def create_word(
    body: WordCreateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """创建词条（直接发布）。"""
    if body.risk_level not in ("low", "medium", "high"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="risk_level 取值非法")
    if db.get(Category, body.category_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")

    word = Word(
        word=body.word,
        pinyin=body.pinyin,
        meaning=body.meaning,
        example=body.example,
        origin=body.origin,
        category_id=body.category_id,
        risk_level=body.risk_level,
        status="published",
        source="manual",
        created_by=None,
        created_by_admin_id=admin.id,
    )
    db.add(word)
    db.commit()
    db.refresh(word)
    return BaseResponse(data={"id": word.id, "word": word.word, "status": word.status})


@router.put("/batch-status", response_model=BaseResponse)
async def batch_update_status(
    body: BatchStatusRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:audit")),
) -> BaseResponse:
    """批量审核状态变更。"""
    if body.status not in ("published", "approved", "rejected", "pending"):
        raise HTTPException(status_code=422, detail="status 取值非法")
    count = db.execute(
        select(func.count()).select_from(
            select(Word).where(Word.id.in_(body.ids), Word.deleted_at.is_(None)).subquery()
        )
    ).scalar_one()
    db.execute(
        update(Word).where(Word.id.in_(body.ids), Word.deleted_at.is_(None)).values(status=body.status)
    )
    db.commit()
    return BaseResponse(data={"updated": count, "status": body.status})


@router.delete("/batch", response_model=BaseResponse)
async def batch_delete_words(
    body: BatchDeleteRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """批量软删除词条。"""
    now = datetime.now(timezone.utc)
    count = db.execute(
        select(func.count()).select_from(
            select(Word).where(Word.id.in_(body.ids), Word.deleted_at.is_(None)).subquery()
        )
    ).scalar_one()
    db.execute(
        update(Word).where(Word.id.in_(body.ids), Word.deleted_at.is_(None)).values(deleted_at=now)
    )
    db.commit()
    return BaseResponse(data={"deleted": count})


class WordBatchItem(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    meaning: str = Field(..., min_length=1)
    category_name: str = Field(..., min_length=1)
    pinyin: str | None = None
    risk_level: str = Field("low", description="low/medium/high")
    example: str | None = None


class WordBatchRequest(BaseModel):
    items: list[WordBatchItem] = Field(..., min_length=1, max_length=1000)


@router.post("/batch", response_model=BaseResponse)
async def batch_create_words(
    body: WordBatchRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """批量创建词条（导入后 status=pending，需审核）。

    - category_name 不存在时自动创建一级分类
    - 同分类下 word 已存在（published/pending 且未软删除）则跳过
    - 返回 success_count / skipped_count / failed_count / failures
    """
    # 预加载所有分类到 dict（name -> Category）
    categories = db.execute(select(Category)).scalars().all()
    category_map: dict[str, Category] = {c.name: c for c in categories}

    # 预加载已存在 word（published/pending 且未软删除），按 (category_id, word) 去重
    existing_rows = db.execute(
        select(Word.category_id, Word.word).where(
            Word.status.in_(["published", "pending"]),
            Word.deleted_at.is_(None),
        )
    ).all()
    existing_set: set[tuple[int, str]] = {(row[0], row[1]) for row in existing_rows}

    success_count = 0
    skipped_count = 0
    failed_count = 0
    failures: list[dict] = []

    for idx, item in enumerate(body.items, start=1):
        # 校验 risk_level
        if item.risk_level not in ("low", "medium", "high"):
            failed_count += 1
            failures.append({"row": idx, "word": item.word, "reason": f"risk_level 非法：{item.risk_level}"})
            continue

        # 查/建分类
        category = category_map.get(item.category_name)
        if category is None:
            category = Category(
                name=item.category_name,
                parent_id=None,
                level=1,
                sort_order=0,
            )
            db.add(category)
            db.flush()  # 获取 id
            category_map[item.category_name] = category

        # 去重检查
        dedup_key = (category.id, item.word)
        if dedup_key in existing_set:
            skipped_count += 1
            continue

        # 创建 Word
        word = Word(
            word=item.word,
            pinyin=item.pinyin,
            meaning=item.meaning,
            example=item.example,
            category_id=category.id,
            risk_level=item.risk_level,
            status="pending",
            source="manual",
            created_by=None,
            created_by_admin_id=admin.id,
        )
        db.add(word)
        existing_set.add(dedup_key)
        success_count += 1

    db.commit()

    return BaseResponse(data={
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "failures": failures,
    })


@router.get("/{word_id}", response_model=BaseResponse)
async def get_word(
    word_id: int,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """词条详情。"""
    service = WordService()
    detail = service.get_detail(word_id, db)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="词条不存在")
    return BaseResponse(data=detail)


@router.put("/{word_id}", response_model=BaseResponse)
async def update_word(
    word_id: int,
    body: WordUpdateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """更新词条。"""
    if body.category_id is not None and db.get(Category, body.category_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    service = WordService()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        word = service.update(word_id, db, **fields)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return BaseResponse(data={"id": word.id, "updated_at": word.updated_at.isoformat() if word.updated_at else None})


@router.delete("/{word_id}", response_model=BaseResponse)
async def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """删除词条（软删除）。"""
    service = WordService()
    try:
        service.delete(word_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return BaseResponse(data={"id": word_id, "deleted_at": datetime.now(timezone.utc).isoformat()})


@router.put("/{word_id}/status", response_model=BaseResponse)
async def update_word_status(
    word_id: int,
    body: WordStatusRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:audit")),
) -> BaseResponse:
    """审核状态变更（发布/下架/拒绝）。"""
    if body.status not in ("published", "approved", "rejected", "pending"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status 取值非法")
    word = db.get(Word, word_id)
    if word is None or word.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="词条不存在")
    word.status = body.status
    db.commit()
    return BaseResponse(data={"id": word.id, "status": word.status})


@router.put("/{word_id}/risk", response_model=BaseResponse)
async def update_word_risk(
    word_id: int,
    body: WordRiskRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:word:manage")),
) -> BaseResponse:
    """标记词条风险。"""
    if body.risk_level not in ("low", "medium", "high"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="risk_level 取值非法")
    word = db.get(Word, word_id)
    if word is None or word.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="词条不存在")
    word.risk_level = body.risk_level
    word.risk_types = body.risk_types
    word.risk_advice = body.advice
    db.commit()
    return BaseResponse(data={"id": word.id, "risk_level": word.risk_level})
