from pydantic_settings import BaseSettings
from pydantic import SecretStr
from typing import Optional

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: SecretStr
    BOT_WEBHOOK_URL: str
    BOT_WEBHOOK_SECRET: SecretStr
    TELEGRAM_BOT_INTERNAL_SECRET: SecretStr

    # Java Backend API
    MAIN_API_BASE_URL: str = "http://app:8081/users"
    MAIN_API_BACKEND_SECRET: SecretStr
    
    # Redis
    REDIS_HOST: str = "telegram-bot-redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    STORAGE_TYPE: str = "redis"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bot_db.sqlite"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()