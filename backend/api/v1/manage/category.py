"""分类管理接口（后台）

- GET    /manage/categories：分类树
- POST   /manage/categories：创建分类
- PUT    /manage/categories/{id}：更新分类
- DELETE /manage/categories/{id}：删除分类

权限：content:category:manage
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db
from core.rbac import require_permission
from models.admin import AdminAccount
from models.category import Category
from models.word import Word
from schemas import BaseResponse

router = APIRouter(prefix="/categories", tags=["分类管理"])


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    parent_id: int | None = Field(None, gt=0)
    icon: str | None = None
    sort_order: int = 0


class CategoryUpdateRequest(BaseModel):
    name: str | None = None
    icon: str | None = None
    sort_order: int | None = None


def _build_tree(categories: list[Category]) -> list[dict]:
    """构建分类树。"""
    nodes = {c.id: {
        "id": c.id, "name": c.name, "parent_id": c.parent_id,
        "level": c.level, "icon": c.icon, "sort_order": c.sort_order,
        "children": [],
    } for c in categories}
    roots = []
    for c in categories:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("", response_model=BaseResponse)
async def list_categories(
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:category:manage")),
) -> BaseResponse:
    """分类树。"""
    cats = db.execute(select(Category).order_by(Category.level, Category.sort_order)).scalars().all()
    return BaseResponse(data={"tree": _build_tree(cats), "total": len(cats)})


@router.post("", response_model=BaseResponse)
async def create_category(
    body: CategoryCreateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:category:manage")),
) -> BaseResponse:
    """创建分类。"""
    level = 1
    if body.parent_id:
        parent = db.get(Category, body.parent_id)
        if parent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="父分类不存在")
        if parent.level >= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="最多支持三级分类")
        level = parent.level + 1

    cat = Category(name=body.name, parent_id=body.parent_id, level=level, icon=body.icon, sort_order=body.sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return BaseResponse(data={"id": cat.id, "name": cat.name, "level": cat.level})


@router.put("/{category_id}", response_model=BaseResponse)
async def update_category(
    category_id: int,
    body: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:category:manage")),
) -> BaseResponse:
    """更新分类。"""
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    if body.name is not None:
        cat.name = body.name
    if body.icon is not None:
        cat.icon = body.icon
    if body.sort_order is not None:
        cat.sort_order = body.sort_order
    db.commit()
    return BaseResponse(data={"id": cat.id, "updated_at": cat.updated_at.isoformat() if cat.updated_at else None})


@router.delete("/{category_id}", response_model=BaseResponse)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: AdminAccount = Depends(require_permission("content:category:manage")),
) -> BaseResponse:
    """删除分类（有子分类或词条时拒绝）。"""
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    # 检查子分类
    child_count = db.execute(
        select(func.count(Category.id)).where(Category.parent_id == category_id)
    ).scalar_one()
    if child_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先删除子分类")
    # 检查关联词条
    word_count = db.execute(
        select(func.count(Word.id)).where(Word.category_id == category_id, Word.deleted_at.is_(None))
    ).scalar_one()
    if word_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"分类下有 {word_count} 个词条，请先迁移")
    db.delete(cat)
    db.commit()
    return BaseResponse(data={"id": category_id, "deleted": True})
