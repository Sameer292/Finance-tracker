from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from schemas.schemas import Transaction
from db import models
from db.database import get_db
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()
security = HTTPBearer()

@router.post('/transactions')
def post_transactions(request:Request, transaction:Transaction, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = request.state.user.id
    new_transaction = models.Transaction(type=transaction.type, amount=transaction.amount, user_id=user_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return{
        'id': new_transaction.id,
        'message': "New transaction added"
    }


@router.get('/transactions')
def get_transactions(request:Request, db:Session=Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    userId = request.state.user.id
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == userId).all()
    return{
        "transactions": transactions
    }
