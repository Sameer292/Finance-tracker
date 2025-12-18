from passlib.context import CryptContext
from datetime import timedelta, datetime
from src.settings import settings
import jwt
import uuid
import logging


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 15


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_data: dict, expiry: timedelta = None, refresh: bool = False
):
    payload = {}
    payload["user"] = user_data
    payload["exp"] = datetime.now() + (
        expiry if expiry is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh
    token = jwt.encode(
        payload=payload, key=settings.JWT_SECRET, algorithm=settings.JWT_ALOGRITHM
    )
    return token


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
        jwt=token, 
        key=settings.JWT_SECRET, 
        algorithms=[settings.JWT_ALOGRITHM]
    )
        return token_data
    except jwt.PyJWTError as e: 
        logging.exception("Error decoding token")
        return None
