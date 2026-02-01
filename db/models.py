from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Numeric
from sqlalchemy.orm import declarative_base, relationship
import enum
import datetime
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

Base = declarative_base()


class TransactionType(str, enum.Enum):
    expense = "expense"
    income = "income"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    current_balance = Column(Numeric(10, 2), default=0)
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    categories = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    total_transactions = Column(Integer, default=0)
    total_expenses = Column(Numeric(10, 2), default=0)
    total_income = Column(Numeric(10, 2), default=0)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(
        Enum(TransactionType, name="transaction_type_enum"), nullable=False
    )
    amount = Column(Numeric(10, 2), nullable=False)
    note = Column(String, nullable=True)
    transaction_date = Column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    user = relationship("User", back_populates="transactions")
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    category = relationship("Category", back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_category_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    color = Column(String)
    icon = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
