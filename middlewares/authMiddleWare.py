from fastapi import Request
from fastapi.responses import JSONResponse
from db import models
from jwt import decode, DecodeError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from db.database import get_db

SECRET = "honey_bunny"  # Move this to env

def get_user_from_token( token: str, db: Session ):
    try:
        payload = decode(token, SECRET, algorithms=["HS256"])
        user_id = payload.get("id")
        if not user_id:
            return None
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
    except DecodeError:
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch( _, request: Request, call_next):
        db = next(get_db())
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user = get_user_from_token(token, db)

            if user:
                request.state.user = user  # attach user to request
            else:
                return JSONResponse({"detail": "Invalid token"}, status_code=401)
        else:
            request.state.user = None  # no token

        return await call_next(request)
