from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from src.settings import settings
import jwt
import uuid
from datetime import date, time,datetime,timezone

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")



def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    refresh: bool = False,
    expiry: timedelta = None,
) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc)
        + (expiry if expiry else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
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
       
        nepal_time= datetime.fromtimestamp(ms / 1000)
        utc_time = nepal_time.replace(microsecond=0, tzinfo=timezone.utc)
        return utc_time

def get_top_categories(transactions, categories):
    
    category_map = {c.id: c.name for c in categories}

    summary_income={}
    summary_expense={}

    for t in transactions:
        category_name = category_map.get(t.category_id, "Other")
        
        if t.transaction_type == 'income':
            summary_income.setdefault(category_name, {"category": category_name, "amount": 0})
            summary_income[category_name]["amount"] += t.amount
        else:
            summary_expense.setdefault(category_name, {"category": category_name, "amount": 0})
            summary_expense[category_name]["amount"] += t.amount
    
    income_sorted = sorted(summary_income.values(), key=lambda x: x["amount"], reverse=True)
    top4_income = income_sorted[:4]
    other_income = {"category": "Other", "amount": sum(x["amount"] for x in income_sorted[4:])} if len(income_sorted) > 4 else None
    if other_income:
       top4_income.append(other_income)

    expense_sorted = sorted(summary_expense.values(), key=lambda x: x["amount"], reverse=True)
    top4_expense = expense_sorted[:4]
    other_expense = {"category": "Other", "amount": sum(x["amount"] for x in expense_sorted[4:])} if len(expense_sorted) > 4 else None
    if other_expense:
       top4_expense.append(other_expense)

    return top4_income, top4_expense