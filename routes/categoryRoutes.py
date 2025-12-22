from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.schemas import Category, AllCategories, FinanceSummaryResponse
from db import models
from schemas.schemas import Transaction, CategoryTransactionResponse
from datetime import date, timedelta, datetime, time

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
    user = getattr(request.state, "user", None)
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
    
    category_map = {c.id: c.name for c in categories}

    summary_income={}
    summary_expense={}

    for t in transactions:
        category_name = category_map.get(t.category_id, "Other")
        
        if t.transaction_type == 'income':
            summary_income.setdefault(category_name, {"category": category_name, "income": 0})
            summary_income[category_name]["income"] += t.amount
        else:
            summary_expense.setdefault(category_name, {"category": category_name, "expense": 0})
            summary_expense[category_name]["expense"] += t.amount
    
    income_sorted = sorted(summary_income.values(), key=lambda x: x["income"], reverse=True)
    top4_income = income_sorted[:4]
    other_income = {"category": "Other", "income": sum(x["income"] for x in income_sorted[4:])} if len(income_sorted) > 4 else None
    if other_income:
       top4_income.append(other_income)

    expense_sorted = sorted(summary_expense.values(), key=lambda x: x["expense"], reverse=True)
    top4_expense = expense_sorted[:4]
    other_expense = {"category": "Other", "expense": sum(x["expense"] for x in expense_sorted[4:])} if len(expense_sorted) > 4 else None
    if other_expense:
       top4_expense.append(other_expense)
        
    Top_Income = top4_income
    Top_Expense = top4_expense

    return {
        "income": Top_Income,
        "expense": Top_Expense
    }