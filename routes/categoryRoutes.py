from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.schemas import Category, AllCategories
from db import models
from schemas.schemas import CategoryTransactionResponse
from middlewares.authMiddleWare import get_current_user

router = APIRouter()
security = HTTPBearer()


@router.get("/categories", response_model=AllCategories, status_code=status.HTTP_200_OK)
def get_categories(
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    user_id = currentUser.id
    categories = (
        db.query(models.Category).filter(models.Category.user_id == user_id).all()
    )
    if not categories:
        raise HTTPException(status_code=404, detail="Categories not found")

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
    category = (
        db.query(models.Category)
        .filter(models.User.id == currentUser.id, models.Category.id == id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    transactions = (
        db.query(models.Transaction)
        .filter(models.User.id == currentUser.id, models.Transaction.category_id == id)
        .all()
    )
    return {"transactions": transactions}


@router.get("/category/{id}", status_code=status.HTTP_200_OK)
def getCategory(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    category = (
        db.query(models.Category)
        .filter(models.user.id == currentUser.id, models.Category.id == id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/categories")
def add_category(
    category: Category,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
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


@router.delete("/category/{id}", status_code=status.HTTP_200_OK)
def deleteCategory(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    category_to_delete = (
        db.query(models.Category)
        .filter(models.user.id == currentUser.id, models.Category.id == id)
        .first()
    )

    if not category_to_delete:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category_to_delete)
    db.commit()
    return {
        "message": "Category deleted successfully",
    }
