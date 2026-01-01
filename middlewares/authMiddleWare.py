from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from db import models
from db.database import get_db
from utils.utils import decode_token
from jwt import DecodeError

security = HTTPBearer()  

# Middleware to attach user to request.state
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db = next(get_db())
        try:
            auth_header = request.headers.get("Authorization")
           
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                user = get_user_from_token(token, db)
                if user:
                    request.state.user = user
                    print("USER:", request.state.user)

                else:
                    return JSONResponse({"message": "Invalid token"}, status_code=401)
            else:
                request.state.user = None

            response = await call_next(request)
            return response
        finally:
            db.close()


# Helper function to decode token and fetch user
def get_user_from_token(token: str, db: Session):
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))  # just to ensure integer
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
    except (KeyError, ValueError, DecodeError):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return db.query(models.User).filter(models.User.id == user_id).first()


# Dependency to protect routes
def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> models.User:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user