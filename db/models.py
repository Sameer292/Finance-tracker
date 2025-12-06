from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import declarative_base, relationship
import enum
import datetime

Base = declarative_base()

class TransactionType(str, enum.Enum):
    expense = "expense"
    income = "income"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    current_balance = Column(Integer, default=0)

    transactions = relationship("Transaction", back_populates="user")
    categories = relationship("Category", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(Enum(TransactionType))
    amount = Column(Integer)
    note = Column(String, nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="transactions")
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category_type = Column(Enum(TransactionType))
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")