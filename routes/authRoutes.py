from fastapi import APIRouter, Depends, status, HTTPException, Body, Request
from db.database import get_db
from db import models
from sqlalchemy.orm import Session
from schemas.schemas import (
    CreateUser,
    Login,
    UserResponse,
    AllUsers,
    RefreshTokenRequest,
)
from jwt import encode
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.utils import create_access_token, decode_token
from datetime import timedelta
from utils.token_store import save_refresh_token
from utils import utils

router = APIRouter()
security = HTTPBearer()
REFRESH_TOKEN_EXPIRY = 15


@router.post("/register", status_code=status.HTTP_200_OK)
def register(credentials: CreateUser = Body(...), db: Session = Depends(get_db)):
    hashed_password = utils.hash_password(credentials.password)
    new_user = models.User(
        name=credentials.name, email=credentials.email, password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "message": "User created successfully"}


@router.post("/login", status_code=status.HTTP_200_OK)
def login(credentials: Login = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not utils.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    access_token = create_access_token(user_id=user.id)
    refresh_token = create_access_token(
        user_id=user.id,
        refresh=True,
        expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
    )

    save_refresh_token(user.id, refresh_token)  # Save refresh token in JSON
    return {
        "id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
def get_new_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if not payload.get("refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    user_id = int(payload.get('sub'))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(user_id=user.id)
    return {"access_token": access_token}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not request.state.user:
        print(request)
        raise HTTPException(status_code=401, detail="Not authenticated")

    return request.state.user


@router.get("/users", response_model=AllUsers, status_code=status.HTTP_200_OK)
def get_AllUsers(
    db: Session = Depends(get_db),
):
    users = db.query(models.User).all()
    return {"users": users}


@router.post("/seed_me", status_code=status.HTTP_200_OK)
def seed_me(db: Session = Depends(get_db)):
    password = "iamsameer"
    hashed_password = utils.hash_password(password)
    new_user = models.User(
        name="sameer", email="iamsameer@gmail.com", password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(
        user_id=new_user.id
    )
    return {
        "id": new_user.id,
        "message": "User created successfully",
        "accessToken": access_token,
    }
