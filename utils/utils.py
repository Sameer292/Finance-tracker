from passlib.context import CryptContext
from datetime import date, time,datetime,timezone

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def ms_to_utc_nepal(ms: int) -> datetime:
       
        nepal_time= datetime.fromtimestamp(ms / 1000)
        utc_time = nepal_time.replace(microsecond=0, tzinfo=timezone.utc)
        return utc_time