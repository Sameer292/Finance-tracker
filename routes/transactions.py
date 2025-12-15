from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from schemas.schemas import Transaction, RecentTransactionsResponse
from db import models
from db.database import get_db
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timedelta
from typing import List
from schemas.schemas import TransactionResponse


router = APIRouter()
security = HTTPBearer()

@router.post('/transactions')
def post_transactions(request:Request, transaction:Transaction, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(transaction)
    category_id = transaction.category_id
    if category_id is not None:
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    new_transaction = models.Transaction(transaction_type=transaction.transaction_type, amount=transaction.amount, note=transaction.note, user_id=user_id, category_id=category_id)
    db.add(new_transaction)
    user.current_balance += transaction.amount if transaction.transaction_type == "income" else -transaction.amount
    db.commit()
    db.refresh(new_transaction)
    db.refresh(user)
    return{
        'id': new_transaction.id,
        'message': "New transaction added",
        'userStatus': 'new balance: ' + str(user.current_balance)
    }


@router.get('/transactions')
def get_transactions(request:Request, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    userId = request.state.user.id
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == userId).all()
    return{
        "transactions": transactions
    }


@router.get("/transactions/recent", response_model=List[TransactionResponse])
def get_recent_transactions(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Get user ID from request state
    user_id = getattr(request.state.user, "id", None)
    
    # Last 3 days
    start_date = datetime.utcnow() - timedelta(days=3)

    # Query transactions of this user in last 3 days
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
        raise HTTPException(status_code=404, detail="No recent transactions found")
   
    return transactions 

@router.get('/transactions/{id}')
def get_transaction(request:Request, id:int, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return{
        "transaction": transaction
    }

@router.delete('/transactions/{id}')
def delete_transaction(request:Request, id: int, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    user_id = request.state.user.id
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.current_balance -= transaction.amount if transaction.transaction_type == "income" else transaction.amount
    db.delete(transaction)
    db.commit()
    return{
        "message": "Transaction deleted"
    }

@router.delete('/transactions')
def delete_all_transactions(request:Request, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    db.query(models.Transaction).delete()
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user.current_balance = 0
    db.commit()
    return{
        "message": "All transactions deleted"
    }

@router.put('/transactions/{id}')
def update_transaction(request:Request, id:int, transaction:Transaction, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    queried_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    user_id = request.state.user.id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    amount_delta = transaction.amount - queried_transaction.amount
    user.current_balance -= amount_delta if queried_transaction.transaction_type == "income" else amount_delta
    queried_transaction.transaction_type = transaction.transaction_type
    queried_transaction.amount = transaction.amount
    db.commit()
    return{
        "message": "Transaction updated"
    }

@router.get("/transactions/last/{days}")
def get_transactions_last_days(
    days: int,
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = request.state.user.id

    start_date = datetime.utcnow() - timedelta(days=days)

    transactions = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.created_date >= start_date
        )
        .all()
    )

    return {
        "days": days,
        "transactions": transactions
    }








