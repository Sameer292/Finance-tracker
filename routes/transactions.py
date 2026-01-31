from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.schemas import Transaction
from db import models
from db.database import get_db
from fastapi.security import HTTPBearer
from typing import Optional
from datetime import datetime, timedelta
from schemas.schemas import (
    FilteredTransactionResponse,
    RecentTransactionsResponse,
    SingleTransactionResponse,
)
from utils import utils
from middlewares.authMiddleWare import get_current_user


router = APIRouter()
security = HTTPBearer()


@router.get(
    "/transactions",
    response_model=FilteredTransactionResponse,
    status_code=status.HTTP_200_OK,
)
def get_transactions(
    start_date_ms: Optional[int] = None,
    end_date_ms: Optional[int] = None,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    if start_date_ms is not None and start_date_ms < 0:
        raise HTTPException(status_code=400, detail="start_date_ms must be positive")
    if end_date_ms is not None and end_date_ms < 0:
        raise HTTPException(status_code=400, detail="end_date_ms must be positive")

    start_date = (
        utils.ms_to_utc_nepal(start_date_ms) if start_date_ms is not None else None
    )
    end_date = utils.ms_to_utc_nepal(end_date_ms) if end_date_ms is not None else None

    # it must be exactly here for the reason of original values
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date cannot be greater than end_date"
        )

    user_id = currentUser.id
    query = db.query(models.Transaction).filter(models.Transaction.user_id == user_id)

    if start_date:
        start_date = start_date.replace(hour=0, minute=0, second=0)
        query = query.filter(models.Transaction.created_date >= start_date)

    if end_date:
        end_date = end_date.replace(hour=0, minute=0, second=0)
        end_date += timedelta(days=1)
        query = query.filter(models.Transaction.created_date < end_date)

    transactions = query.order_by(models.Transaction.created_date.desc()).all()

    if start_date_ms is None and end_date_ms is None:
        return {"transactions": transactions}
    return {
        "start_date_ms": start_date_ms,
        "end_date_ms": end_date_ms,
        "transactions": transactions,
    }


@router.get(
    "/transactions/recent",
    response_model=RecentTransactionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_recent_transactions(
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    user_id = currentUser.id

    start_date = datetime.utcnow() - timedelta(days=3)
    transactions = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.created_date >= start_date,
        )
        .order_by(models.Transaction.created_date.desc())
        .all()
    )
    if not transactions:
        return {"message": "No recent transactions found", "transactions": []}
    return {
        "message": "Recent transactions retrieved successfully",
        "transactions": transactions,
    }


@router.get(
    "/transactions/{id}",
    response_model=SingleTransactionResponse,
    status_code=status.HTTP_200_OK,
)
def get_transaction(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    user_id = currentUser.id
    transaction = (
        db.query(models.Transaction)
        .filter(models.User.id == user_id, models.Transaction.id == id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"transaction": transaction}


@router.post("/transactions")
def post_transactions(
    transaction: Transaction,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    category_id = transaction.category_id
    if category_id is not None:
        category = (
            db.query(models.Category)
            .filter(
                models.Category.id == category_id,
                models.Category.user_id == currentUser.id,
            )
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    new_transaction = models.Transaction(
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        note=transaction.note,
        user_id=currentUser.id,
        category_id=category_id,
        transaction_date=transaction.transaction_date,
    )

    db.add(new_transaction)
    currentUser.total_transactions += 1
    if transaction.transaction_type == "expense":
        currentUser.total_expenses += transaction.amount
        currentUser.current_balance -= transaction.amount
    else:
        currentUser.total_income += transaction.amount
        currentUser.current_balance += transaction.amount
    db.commit()
    db.refresh(new_transaction)
    db.refresh(currentUser)
    return {
        "id": new_transaction.id,
        "message": "New transaction added",
        "userStatus": "new balance: " + str(currentUser.current_balance),
    }


@router.put("/transactions/{id}")
def update_transaction(
    id: int,
    transaction: Transaction,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    queried_transaction = (
        db.query(models.Transaction).filter(models.Transaction.id == id).first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    amount_delta = transaction.amount - queried_transaction.amount
    if transaction.category_id is not None:
        category = (
            db.query(models.Category)
            .filter(
                models.Category.id == transaction.category_id,
                models.Category.user_id == currentUser.id,
            )
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        queried_transaction.category_id = transaction.category_id
    queried_transaction.note = transaction.note
    queried_transaction.transaction_date = transaction.transaction_date
    if transaction.transaction_type == "expense":
        currentUser.total_expenses += amount_delta
        currentUser.current_balance -= amount_delta
    else:
        currentUser.total_income += amount_delta
        currentUser.current_balance += amount_delta
    db.commit()
    return {"message": "Transaction updated"}


@router.delete("/transactions/{id}")
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    transaction = (
        db.query(models.Transaction).filter(models.Transaction.id == id).first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.transaction_type == "expense":
        currentUser.total_expenses -= transaction.amount
        currentUser.current_balance += transaction.amount
    else:
        currentUser.total_income -= transaction.amount
        currentUser.current_balance -= transaction.amount
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted"}


@router.delete("/transactions")
def delete_all_transactions(
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    db.query(models.Transaction).delete()
    currentUser.current_balance = 0
    currentUser.total_expenses = 0
    currentUser.total_income = 0
    db.commit()
    return {"message": "All transactions deleted"}
