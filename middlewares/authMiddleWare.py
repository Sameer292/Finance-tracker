from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from db import models
from jwt import decode, DecodeError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from db.database import get_db
from utils.utils import decode_token


def get_user_from_token(token: str, db: Session):
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        if not user_id:
            return None
    except HTTPException:
        return None
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
    except Exception:
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db = next(get_db())
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user = get_user_from_token(token, db)
            if user:
                request.state.user = user
            else:
                return JSONResponse({"detail": "Invalid token"}, status_code=401)
        else:
            request.state.user = None
        try:
            response = await call_next(request)
            return response
        finally:
            db.close()