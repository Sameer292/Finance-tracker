from pydantic import BaseModel
from enum import Enum


class TransactionType(str, Enum):
    INCOME = 'income'
    EXPENSES = 'expense'

class Create_User(BaseModel):
    name: str
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class Transaction(BaseModel):
    type: TransactionType
    amount: int

class Me(BaseModel):
    id: int
    email: str
    name: str

    class config:
        orm_mode = True