from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer
from db import models
from db.database import get_db
from schemas.schemas import (
    Transaction,
    TransactionUpdate,
    FilteredTransactionResponse,
    RecentTransactionsResponse
)
from utils import utils
from middlewares.authMiddleWare import require_auth

router = APIRouter()
security = HTTPBearer()

@router.get("/transactions", response_model=FilteredTransactionResponse, dependencies=[Depends(security)])
def get_transactions(
    start_date_ms: Optional[int] = None,
    end_date_ms: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth)
):
    if start_date_ms is not None and start_date_ms < 0:
        raise HTTPException(status_code=400, detail="start_date_ms must be positive")
    if end_date_ms is not None and end_date_ms < 0:
        raise HTTPException(status_code=400, detail="end_date_ms must be positive")

    start_date = utils.ms_to_utc_nepal(start_date_ms) if start_date_ms else None
    end_date = utils.ms_to_utc_nepal(end_date_ms) if end_date_ms else None

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date")

    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)

    if start_date:
        start_date = start_date.replace(hour=0, minute=0, second=0)
        query = query.filter(models.Transaction.created_date >= start_date)

    if end_date:
        end_date = end_date.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        query = query.filter(models.Transaction.created_date < end_date)

    transactions = query.order_by(models.Transaction.created_date.desc()).all()

    return {
        "transactions": transactions,
        **({"start_date_ms": start_date_ms, "end_date_ms": end_date_ms} if start_date_ms or end_date_ms else {})
    }

@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def post_transaction(
    transaction: Transaction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth),
):
    
    user = db.query(models.User).filter(
        models.User.id == current_user.id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate category ownership
    if transaction.category_id:
        category = db.query(models.Category).filter(
            models.Category.id == transaction.category_id,
            models.Category.user_id == user.id
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    # Create transaction
    new_transaction = models.Transaction(
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        note=transaction.note,
        transaction_date=transaction.transaction_date,
        category_id=transaction.category_id,
        user_id=user.id
    )

    db.add(new_transaction)

    # Update balance safely
    if transaction.transaction_type == "income":
        user.current_balance += transaction.amount
    else:
        user.current_balance -= transaction.amount

    db.commit()
    db.refresh(new_transaction)
    db.refresh(user)

    return {
        "id": new_transaction.id,
        "message": "Transaction added successfully",
        "userStatus": f"new balance: {user.current_balance}"
    }

@router.get("/transactions/recent", response_model=RecentTransactionsResponse)
def get_recent_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth)
):
    start_date = datetime.utcnow() - timedelta(days=3)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.created_date >= start_date
    ).order_by(models.Transaction.created_date.desc()).all()

    return {
        "message": "Recent transactions retrieved successfully" if transactions else "No recent transactions found",
        "transactions": transactions
    }

@router.patch("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth)
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    if "amount" in update_data:
        if update_data["amount"] is None:
            raise HTTPException(status_code=400, detail="Amount cannot be null")
        if update_data["amount"] < 0:
            raise HTTPException(status_code=400, detail="Amount cannot be negative")

    if "category_id" in update_data:
        category = db.query(models.Category).filter(
            models.Category.id == update_data["category_id"],
            models.Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category_id")

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return {"message": "Transaction updated successfully", "transaction_id": transaction.id}


@router.get("/transactions/{id}")
def get_transaction(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth)
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == id,
        models.Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"transaction": transaction}

@router.delete("/transactions/{id}")
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth)
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == id,
        models.Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    current_user.current_balance -= transaction.amount if transaction.transaction_type == "income" else transaction.amount
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}


@router.delete("/transactions")
def delete_all_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_auth)
):
    db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).delete(synchronize_session=False)
    current_user.current_balance = 0
    db.commit()
    return {"message": "All transactions deleted successfully"}
