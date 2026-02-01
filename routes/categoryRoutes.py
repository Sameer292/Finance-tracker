from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from db import models
from schemas.categorySchemas import (
    Category,
    AllCategories,
    CategoryTransactionResponse,
    CategoryResponse,
    AddCategoryResponse,
    DeleteAllCategoriesResponse,
)
from middlewares.authMiddleWare import get_current_user

router = APIRouter()

@router.get("/categories", response_model=AllCategories, status_code=status.HTTP_200_OK)
def get_categories(
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    categories = db.query(models.Category).filter(models.Category.user_id == currentUser.id).all()
    return {"categories": categories}


@router.get(
    "/category/{id}/transactions",
    response_model=CategoryTransactionResponse,
    status_code=status.HTTP_200_OK,
)
def category_transactions(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    category = db.query(models.Category).filter(
        models.Category.id == id,
        models.Category.user_id == currentUser.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    transactions = db.query(models.Transaction).filter(
        models.Transaction.category_id == id,
        models.Transaction.user_id == currentUser.id
    ).all()

    return {"category_id": category.id, "transactions": transactions}


@router.get(
    "/category/{id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK
)
def get_category(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    category = db.query(models.Category).filter(
        models.Category.id == id,
        models.Category.user_id == currentUser.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post(
    "/categories",
    response_model=AddCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_category(
    category: Category,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    existing = db.query(models.Category).filter(
        models.Category.user_id == currentUser.id,
        models.Category.name == category.name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category name already exists")

    new_category = models.Category(
        name=category.name,
        user_id=currentUser.id,
        color=category.color,
        icon=category.icon,
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"id": new_category.id, "message": "New category added"}


@router.delete(
    "/category/{id}",
    response_model=DeleteAllCategoriesResponse,
    status_code=status.HTTP_200_OK,
)
def delete_category(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    category_to_delete = db.query(models.Category).filter(
        models.Category.id == id,
        models.Category.user_id == currentUser.id
    ).first()

    if not category_to_delete:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category_to_delete)
    db.commit()
    return {"message": "Category deleted successfully"}
