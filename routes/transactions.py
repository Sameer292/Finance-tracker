from fastapi import APIRouter, Depends, Request, HTTPException,status
from sqlalchemy.orm import Session
from schemas.schemas import Transaction
from db import models
from db.database import get_db
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from datetime import datetime, timedelta
from schemas.schemas  import FilteredTransactionResponse, RecentTransactionsResponse
from utils import utils

router = APIRouter()
security = HTTPBearer()


@router.get("/transactions", response_model=FilteredTransactionResponse)
def get_transactions(
    request: Request,
    start_date_ms: Optional[int] = None,
    end_date_ms: Optional[int] = None,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
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

    user_id = request.state.user.id
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


@router.post("/transactions")
def post_transactions(
    request: Request,
    transaction: Transaction,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    category_id = transaction.category_id
    if category_id is not None:
        category = (
            db.query(models.Category).filter(models.Category.id == category_id, models.Category.user_id == user_id).first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    new_transaction = models.Transaction(
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        note=transaction.note,
        user_id=user_id,
        category_id=category_id,
        transaction_date=transaction.transaction_date,
    )
    
    
    db.add(new_transaction)
    user.current_balance += (
        transaction.amount
        if transaction.transaction_type == "income"
        else -transaction.amount
    )
    db.commit()
    db.refresh(new_transaction)
    db.refresh(user)
    return {
        "id": new_transaction.id,
        "message": "New transaction added",
        "userStatus": "new balance: " + str(user.current_balance),
    }

@router.get(
    "/transactions/recent",
    response_model=RecentTransactionsResponse,
    status_code=status.HTTP_200_OK
)
def get_recent_transactions(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = request.state.user.id

    start_date = datetime.utcnow() - timedelta(days=3)
    transactions = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.created_date >= start_date
        )
        .order_by(models.Transaction.created_date.desc())
        .all()
    )
    if not transactions:
        return {
            "message":"No recent transactions found",
            "transactions":[]
        }
    return {

        "message":"Recent transactions retrieved successfully",
        "transactions":transactions
    }

@router.get("/transactions/{id}")
def get_transaction(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    transaction = (
        db.query(models.Transaction).filter(models.Transaction.id == id).first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"transaction": transaction}


@router.delete("/transactions/{id}")
def delete_transaction(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    transaction = (
        db.query(models.Transaction).filter(models.Transaction.id == id).first()
    )
    user_id = request.state.user.id
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.current_balance -= (
        transaction.amount
        if transaction.transaction_type == "income"
        else transaction.amount
    )
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted"}



@router.delete("/transactions")
def delete_all_transactions(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    db.query(models.Transaction).delete()
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.current_balance = 0
    db.commit()
    return {"message": "All transactions deleted"}


@router.put("/transactions/{id}")
def update_transaction(
    request: Request,
    id: int,
    transaction: Transaction,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    queried_transaction = (
        db.query(models.Transaction).filter(models.Transaction.id == id).first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    amount_delta = transaction.amount - queried_transaction.amount
    user.current_balance -= (
        amount_delta
        if queried_transaction.transaction_type == "income"
        else amount_delta
    )
    queried_transaction.transaction_type = transaction.transaction_type
    queried_transaction.amount = transaction.amount
    db.commit()
    return {"message": "Transaction updated"}

