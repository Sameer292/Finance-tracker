from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import datetime,date
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
    transaction_date: date | None = None

    @field_validator("transaction_date", mode="before")
    @classmethod
    def convert_to_datetime(cls, v):
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())  # convert date → datetime
        if isinstance(v, str):
            # handle string just in case
            return datetime.strptime(v, "%Y-%m-%d")
        return v


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
    color: str
    icon: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    color: str
    icon: str


class AllCategories(BaseModel):
    categories: list[CategoryResponse]




class TransactionResponse(BaseModel):
    id: int
    transaction_type: TransactionType 
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

class CategoryTransactionResponse(BaseModel):
    transactions: list[Transaction]

