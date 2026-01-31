from fastapi import APIRouter, Depends, status, HTTPException, Body
from db.database import get_db
from db import models
from sqlalchemy.orm import Session
from schemas.schemas import (
    CreateUser,
    Login,
    UserResponse,
    AllUsers,
    RefreshTokenRequest,
    LoginResponse,
    ChangePasswordResponse,
    RefreshResponse,
    ChangePassword,
    UpdateProfile,
    RegisterResponse,
)
from fastapi.security import HTTPBearer
from utils.utils import create_access_token, decode_token
from datetime import timedelta
from utils import utils
from src.settings import settings
from middlewares.authMiddleWare import get_current_user
from email_validator import validate_email, EmailNotValidError

router = APIRouter()
security = HTTPBearer()


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(
    currentUser: models.User = Depends(get_current_user),
):
    return currentUser


@router.get("/users", response_model=AllUsers, status_code=status.HTTP_200_OK)
def get_AllUsers(
    db: Session = Depends(get_db),
):
    users = db.query(models.User).all()
    return {"users": users}


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_200_OK
)
def register(credentials: CreateUser = Body(...), db: Session = Depends(get_db)):
    try:
        emailInfo = validate_email(credentials.email, check_deliverability=True)
        email = emailInfo.normalized
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email")
    hashed_password = utils.hash_password(credentials.password)
    new_user = models.User(name=credentials.name, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "message": "User created successfully"}


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(credentials: Login = Body(...), db: Session = Depends(get_db)):
    email = validate_email(credentials.email, check_deliverability=False).normalized
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not utils.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user_id=user.id)
    refresh_token = create_access_token(
        user_id=user.id,
        refresh=True,
        expiry=timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS),
    )

    return {
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
def get_new_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if not payload.get("refresh") or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user_id = int(payload.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(user_id=user.id)
    return {"user_id": user.id, "access_token": access_token}


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
    access_token = create_access_token(user_id=new_user.id)
    return {
        "id": new_user.id,
        "message": "User created successfully",
        "accessToken": access_token,
    }


@router.put(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
)
def change_password(
    password_data: ChangePassword = Body(...),
    currentUser: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not utils.verify_password(password_data.current_password, currentUser.password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    currentUser.password = utils.hash_password(password_data.new_password)
    db.commit()
    accessToken = create_access_token(user_id=currentUser.id)

    return {"message": "Password changed successfully", "accessToken": accessToken}


@router.patch("/update-profile", status_code=status.HTTP_200_OK)
def update_profile(
    update_data: UpdateProfile,
    db: Session = Depends(get_db),
    currentUser: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == currentUser.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if update_data.name:
        user.name = update_data.name

    if update_data.email:
        user.email = update_data.email

    db.commit()

    return {"message": "Profile updated successfully", "userId": user.id}
