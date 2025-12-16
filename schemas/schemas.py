from pydantic import BaseModel
from enum import Enum
from datetime import datetime, date


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

class CategoryTransactionResponse(BaseModel):
    transactions: list[Transaction]
