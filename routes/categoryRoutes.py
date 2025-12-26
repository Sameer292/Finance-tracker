from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.schemas import Category, AllCategories, FinanceSummaryResponse
from db import models
from schemas.schemas import Transaction, CategoryTransactionResponse
from datetime import date, timedelta, datetime, time
from utils.utils import get_top_categories

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

@router.get('/finance-summary', status_code=status.HTTP_200_OK, response_model=FinanceSummaryResponse)
def get_summary(request: Request, db: Session = Depends(get_db), 
                credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = request.state.user
    if not user:
     raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user.id
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)

    start_date = datetime.combine(first_day_last_month, time.min)
    end_date   = datetime.combine(last_day_last_month, time.max)
    
    categories = db.query(models.Category).filter(models.Category.user_id == user_id).all()
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == user_id,
    models.Transaction.transaction_date >= start_date,
    models.Transaction.transaction_date <= end_date,  
    ).all()
    
    Top_Income, Top_Expense = get_top_categories(transactions, categories);

    return {
    "summary": {
        "income": Top_Income,
        "expense": Top_Expense
    }
}