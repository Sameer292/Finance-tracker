from fastapi import Depends, HTTPException
from db import models
from sqlalchemy.orm import Session
from db.database import get_db
from utils.utils import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


def get_user_from_token(token: str, db: Session) -> models.User | None:
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        if not user_id:
            return None
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    token = credentials.credentials
    user = get_user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user
