from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from src.settings import settings
import jwt
import uuid
from datetime import date, time,datetime,timezone
from typing import List, Dict

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


def top_n_and_other_category(summary: Dict[str, Dict], n: int = 4, other_label: str = "Other") -> List[Dict]:
    items = list(summary.values())
    items.sort(key=lambda x: x["amount"], reverse=True)

    top_category = items[:n]
    rest_category = items[n:]

    if rest_category:
        top_category.append({
            "category": other_label,
            "amount": sum(x["amount"] for x in rest_category),
            "totaltransaction": sum(x["totaltransaction"] for x in rest_category),
        })

    return top_category


def get_top_categories(transactions: List[Dict], categories: List[Dict]):
    
    category_map = {c.id: c.name for c in categories}

    summary_income={}
    summary_expense={}

    for t in transactions:
        category_name = category_map.get(t.category_id, "Other")
        
        if t.transaction_type == 'income':
            summary_income.setdefault(category_name, {"category": category_name, "amount": 0, 'totaltransaction': 0})
            summary_income[category_name]["amount"] += t.amount
            summary_income[category_name]["totaltransaction"] += 1
        else:
            summary_expense.setdefault(category_name, {"category": category_name, "amount": 0, 'totaltransaction': 0})
            summary_expense[category_name]["amount"] += t.amount
            summary_expense[category_name]["totaltransaction"] += 1
    
    income_sorted = sorted(summary_income.values(), key=lambda x: x["amount"], reverse=True)
    top4_income = income_sorted[:4]
    other_income = {"category": "Other", "amount": sum(x["amount"] for x in income_sorted[4:])} 
    
    top4_income = top_n_and_other_category(summary_income, n=4, other_label="Other")
    top4_expense = top_n_and_other_category(summary_expense, n=4, other_label="Other")



    return top4_income, top4_expense