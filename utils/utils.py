from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from src.settings import settings
from fastapi import HTTPException, status
from src.settings import settings
import jwt
import uuid

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
