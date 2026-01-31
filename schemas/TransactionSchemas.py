from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import date, datetime
from typing import List, Optional


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


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


class PostTransactionResponse(BaseModel):
    id: int
    message: str
    userStatus: str


class UpdateTransactionResponse(BaseModel):
    transaction_id: int
    message: str


class DeleteTransactionResponse(BaseModel):
    deleted_transaction_id: int
    message: str


class DeleteAllTransactionsResponse(BaseModel):
    message: str


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
