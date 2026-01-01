from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from db import models
from db.database import get_db
from schemas.schemas import Category, Categoryupdate, AllCategories, CategoryTransactionResponse
from middlewares.authMiddleWare import require_auth

router = APIRouter()
security = HTTPBearer()  


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def add_category(
    category: Category,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    new_category = models.Category(
        name=category.name.strip(),
        color=category.color,
        icon=category.icon,
        user_id=current_user.id
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"id": new_category.id, "message": "Category added successfully"}


@router.get("/categories", response_model=AllCategories)
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    categories = db.query(models.Category).filter(models.Category.user_id == current_user.id).all()
    return {"categories": categories}


@router.get("/category/{id}", status_code=status.HTTP_200_OK)
def get_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    category = db.query(models.Category).filter(
        models.Category.id == id,
        models.Category.user_id == current_user.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.get("/category/{id}/transactions", response_model=CategoryTransactionResponse)
def category_transactions(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    category = db.query(models.Category).filter(
        models.Category.id == id,
        models.Category.user_id == current_user.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.category_id == id,
        models.Transaction.user_id == current_user.id
    ).all()
    return {"transactions": transactions}


@router.patch("/categories/{category_id}")
def update_category(
    category_id: int,
    payload: Categoryupdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    for field, value in update_data.items():
        if isinstance(value, str) and not value.strip():
            raise HTTPException(status_code=400, detail=f"{field} cannot be empty")
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return {"message": "Category updated successfully", "category_id": category.id}


@router.delete("/category/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


@router.delete("/categories")
def delete_all_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    # Delete all transactions first
    db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).delete(synchronize_session=False)
    # Delete all categories
    db.query(models.Category).filter(models.Category.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()
    return {"message": "All categories and related transactions deleted"}
