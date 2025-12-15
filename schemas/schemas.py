from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional, List


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class CreateUser(BaseModel):
    name: str
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class Transaction(BaseModel):
    transaction_type: TransactionType
    amount: int
    note: str | None = None
    category_id: int | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    current_balance: int

    class Config:
        from_attributes = True 


class AllUsers(BaseModel):
    users: list[UserResponse]


class Category(BaseModel):
    name: str
    category_type: TransactionType

class CategoryResponse(BaseModel):
    id: int
    name: str
    category_type: TransactionType

class AllCategories(BaseModel):
    categories: list[CategoryResponse]





class TransactionResponse(BaseModel):
    id: int
    transaction_type: str   
    amount: int
    note: Optional[str] = None
    user_id: int
    category_id: Optional[int] = None
    created_date: datetime

    class Config:
        from_attributes = True

class RecentTransactionsResponse(BaseModel):
    type: str
    days: int
    transactions: List[TransactionResponse]