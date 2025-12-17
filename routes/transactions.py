from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from schemas.schemas import Transaction
from db import models
from db.database import get_db
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from datetime import date,time,datetime
from schemas.schemas import FilteredTransactionResponse, TransactionResponse

router = APIRouter()
security = HTTPBearer()

@router.get('/transactions',response_model=FilteredTransactionResponse)
def get_transactions(request:Request,start_date: Optional[date] =None,
                     end_date: Optional[date] =None,
                     db :Session=Depends(get_db),
                     credentials: HTTPAuthorizationCredentials = Depends(security)):
                     user_id =request.state.user.id
                     query= db.query(models.Transaction).filter(models.Transaction.user_id==user_id)
                     if start_date:
                          start_dt=datetime.combine(start_date,time.min)  #00:00:00
                          query=query.filter(models.Transaction.created_date>=start_dt)
                     if end_date:
                          end_dt =datetime.combine(end_date,time.max)  #23:59:59
                          query= query.filter(models.Transaction.created_date<=end_dt)

                     transactions=query.order_by(models.Transaction.created_date.desc()).all()  
                   
                     return{
                    #    "type":"date_filtered",
                       "start_date":start_date,
                       "end_date":end_date,
                       "transactions":transactions 
                   }

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
    new_transaction = models.Transaction(
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        note=transaction.note,
        user_id=user_id,
        category_id=category_id,
        transaction_date=transaction.transaction_date,
    )
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