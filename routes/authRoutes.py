from fastapi import APIRouter, Depends, status, HTTPException, Query, Body, Request, Response
from db.database import get_db
from db import models
from sqlalchemy.orm import Session
from schemas.schemas import Create_User, Login, Me
from utils import utils
from jwt import encode, decode, DecodeError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
SECRET_KEY = "honey_bunny"
security = HTTPBearer()


@router.post("/register", status_code=status.HTTP_200_OK)
def register(credentials: Create_User = Body(...), db: Session = Depends(get_db)):
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

    access_token = encode(key=SECRET_KEY, algorithm="HS256", payload={"id": user.id})
    return {
        "id": user.id,
        "access_token": access_token,
    }


@router.post("/isCorrect")
def isCorrect(accessCode: str = Query(...), db: Session = Depends(get_db)):
    try:
        decode(accessCode, SECRET_KEY, algorithms=["HS256"])
        return {"message": "Access Granted"}
    except DecodeError:
        raise HTTPException(status_code=401, detail="Access Denied")


@router.get('/me', response_model=Me, status_code=status.HTTP_200_OK)
def get_user(request: Request, response:Response, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    return request.state.user