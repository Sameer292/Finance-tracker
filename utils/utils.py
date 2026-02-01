from typing import Optional
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from src.settings import settings
import jwt
import uuid
from db import models
from schemas.TransactionSchemas import Transaction
from decimal import Decimal

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    refresh: bool = False,
    expiry: Optional[timedelta] = None,
) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc)
        + (
            expiry
            if expiry
            else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        ),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return token_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def ms_to_utc_nepal(ms: int) -> datetime:
    nepal_time = datetime.fromtimestamp(ms / 1000)
    utc_time = nepal_time.replace(microsecond=0, tzinfo=timezone.utc)
    return utc_time


def adjust_user_balance(
    user: models.User,
    old_txn: Optional[models.Transaction],
    new_txn: Optional[Transaction],
):
    """
    Adjusts user's balance and totals.
    - old_txn: the previous transaction to rollback
    - new_txn: the new transaction to apply
    """
    # Rollback old transaction effect
    if old_txn:
        if old_txn.transaction_type == "expense":
            user.total_expenses -= old_txn.amount
            user.current_balance += old_txn.amount
        else:
            user.total_income -= old_txn.amount
            user.current_balance -= old_txn.amount

    # Apply new transaction effect
    if new_txn:
        amt = Decimal(new_txn.amount)
        if new_txn.transaction_type == "expense":
            user.total_expenses +=  amt
            user.current_balance -= amt
        else:
            user.total_income += amt
            user.current_balance += amt
