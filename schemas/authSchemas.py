from pydantic import BaseModel, ConfigDict
from typing import Optional


class CreateUser(BaseModel):
    name: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    current_balance: float
    total_transactions: int
    total_expenses: float
    total_income: float
    model_config = ConfigDict(from_attributes=True)

    # class Config:
    #     from_attributes = True


class AllUsers(BaseModel):
    users: list[UserResponse]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class UpdateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class userUpdateResponse(BaseModel):
    user_id: int
    message: str


class LoginResponse(BaseModel):
    user_id: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class RegisterResponse(BaseModel):
    user_id: int
    message: str


class RefreshResponse(BaseModel):
    user_id: int
    access_token: str


class ChangePasswordResponse(BaseModel):
    user_id: int
    message: str
