from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALOGRITHM: str
    access_token_expire_minutes: int = 15

    class Config:
        env_file = ".env"

settings = Settings()