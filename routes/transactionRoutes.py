from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import models
from db.database import get_db
from typing import Optional
from datetime import datetime, timedelta
from schemas.TransactionSchemas import (
    Transaction,
    FilteredTransactionResponse,
    RecentTransactionsResponse,
    SingleTransactionResponse,
    PostTransactionResponse,
    UpdateTransactionResponse,
    DeleteTransactionResponse,
    DeleteAllTransactionsResponse,
)
from utils import utils
from middlewares.authMiddleWare import get_current_user


router = APIRouter()


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
        query = query.filter(models.Transaction.transaction_date >= start_date)

    if end_date:
        end_date = end_date.replace(hour=0, minute=0, second=0)
        end_date += timedelta(days=1)
        query = query.filter(models.Transaction.transaction_date < end_date)

    transactions = query.order_by(models.Transaction.transaction_date.desc()).all()

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
            models.Transaction.transaction_date >= start_date,
        )
        .order_by(models.Transaction.transaction_date.desc())
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
        .filter(models.Transaction.id == id, models.Transaction.user_id == user_id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"transaction": transaction}


@router.post(
    "/transactions",
    response_model=PostTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    utils.adjust_user_balance(currentUser, old_txn=None, new_txn=transaction)
    try:
        db.commit()
    except:
        db.rollback()
        raise
    db.refresh(new_transaction)
    db.refresh(currentUser)
    return {
        "transaction_id": new_transaction.id,
        "current_balance": currentUser.current_balance,
    }


@router.put(
    "/transactions/{id}",
    response_model=UpdateTransactionResponse,
    status_code=status.HTTP_200_OK,
)
def update_transaction(
    id: int,
    transaction: Transaction,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    queried_transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == id,
            models.Transaction.user_id == currentUser.id,
        )
        .first()
    )

    if not queried_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Validate category ownership
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

    utils.adjust_user_balance(
        currentUser, old_txn=queried_transaction, new_txn=transaction
    )

    queried_transaction.amount = transaction.amount
    queried_transaction.transaction_type = transaction.transaction_type
    queried_transaction.note = transaction.note
    queried_transaction.transaction_date = transaction.transaction_date

    try:
        db.commit()
    except:
        db.rollback()
        raise

    return {
        "transaction_id": queried_transaction.id,
        "message": "Transaction updated successfully",
        "current_balance": currentUser.current_balance,
    }


@router.delete(
    "/transactions/{id}",
    response_model=DeleteTransactionResponse,
    status_code=status.HTTP_200_OK,
)
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == id, models.Transaction.user_id == currentUser.id
        )
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    utils.adjust_user_balance(currentUser, old_txn=transaction, new_txn=None)
    db.delete(transaction)
    currentUser.total_transactions -= 1
    try:
        db.commit()
    except:
        db.rollback()
        raise
    return {"deleted_transaction_id": transaction.id, "message": "Transaction deleted"}


@router.delete(
    "/transactions",
    response_model=DeleteAllTransactionsResponse,
    status_code=status.HTTP_200_OK,
)
def delete_all_transactions(
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    db.query(models.Transaction).filter(
        models.Transaction.user_id == currentUser.id
    ).delete()
    currentUser.current_balance = 0
    currentUser.total_expenses = 0
    currentUser.total_income = 0
    currentUser.total_transactions = 0
    try:
        db.commit()
    except:
        db.rollback()
        raise
    return {"message": "All transactions deleted"}
