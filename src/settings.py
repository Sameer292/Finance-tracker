from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRY_DAYS : int
    DATABASE_URL: str

    model_config = ConfigDict(env_file=".env")

settings = Settings()