from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import date, datetime
from typing import List, Optional


class TransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: float
    note: Optional[str] = None
    created_date: datetime
    updated_date: datetime
    category_id: Optional[int] = None
    transaction_date: Optional[datetime] = None

    class Config:
        from_attribute = True


class FilteredTransactionResponse(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_date_ms: Optional[int] = None
    end_date_ms: Optional[int] = None
    transactions: List[TransactionResponse]


class RecentTransactionsResponse(BaseModel):
    message: str
    transactions: List[TransactionResponse]


class SingleTransactionResponse(BaseModel):
    transaction: TransactionResponse


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
    amount: float
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
    current_balance: float
    total_transactions: int
    total_expenses: float
    total_income: float

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


class CategoryTransactionResponse(BaseModel):
    transactions: list[Transaction]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class UpdateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class LoginResponse(BaseModel):
    user_id: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class RegisterResponse(BaseModel):
    user_id: int
    message: str

class RefreshResponse(BaseModel):
    user_id: int
    access_token: str

class ChangePasswordResponse(BaseModel):
    user_id: int
    message: str
