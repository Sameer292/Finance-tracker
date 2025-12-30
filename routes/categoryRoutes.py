from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.schemas import Category, AllCategories
from db import models
from schemas.schemas import Transaction, CategoryTransactionResponse,Categoryupdate

router = APIRouter()
security = HTTPBearer()


@router.post("/categories")
def add_category(
    request: Request,
    category: Category,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_category = models.Category(
        name=category.name, user_id=user.id, color=category.color, icon=category.icon
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"id": new_category.id, "message": "New category added"}


@router.get(
    "/categories", response_model=AllCategories, status_code=status.HTTP_200_OK
)
def get_categories(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = request.state.user.id
    categories = db.query(models.Category).filter(models.Category.user_id == user_id).all()
    if not categories:
        raise HTTPException(status_code=404, detail="Categories not found")
    
    return {"categories": categories}


@router.get("/category/{id}/transactions",response_model=CategoryTransactionResponse, status_code=status.HTTP_200_OK)
def category_transactions(id:int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    transactions = db.query(models.Transaction).filter(models.Transaction.category_id == id).all()
    return {'transactions': transactions }


@router.get("/category/{id}", status_code=status.HTTP_200_OK)
def getCategory(id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.delete("/category/{id}", status_code=status.HTTP_200_OK)
def deleteCategory(id: int, db: Session = Depends(get_db)):
    category_to_delete = db.query(models.Category).filter(models.Category.id == id).first()

    if not category_to_delete:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category_to_delete)
    db.commit()
    return {
        "message": "Category deleted successfully",
    }

@router.delete("/categories")
def delete_all_categories(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = request.state.user.id
    db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(models.Category).filter(
        models.Category.user_id == user_id
    ).delete(synchronize_session=False)
    db.commit()
    return {
        "message": "All categories and related transactions deleted"
        }


@router.patch("/categories/{category_id}")
def update_category(
    request: Request,
    category_id: int,
    payload: Categoryupdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = request.state.user.id

    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == user_id
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
    return {
        "message": "Category updated successfully",
        "category": category
    }
