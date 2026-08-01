import json
from enum import Enum
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Resume Screener & Candidate Ranking SaaS"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            return json.loads(v)
        return v

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    SYNC_DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "SUPER_SECRET_CHANGE_ME_IN_PRODUCTION_1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # OpenAI & LLM Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        # Convert standard postgresql schema to asyncpg for FastAPI async runtime
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Strip sslmode parameters for asyncpg compatibility (preventing unexpected keyword argument 'sslmode')
        if "postgresql" in self.DATABASE_URL:
            if "?sslmode=" in self.DATABASE_URL:
                self.DATABASE_URL = self.DATABASE_URL.split("?sslmode=")[0]
            elif "&sslmode=" in self.DATABASE_URL:
                self.DATABASE_URL = self.DATABASE_URL.split("&sslmode=")[0]

        # Format sync engine DB URL to match and use psycopg2
        if "sqlite" in self.DATABASE_URL:
            self.SYNC_DATABASE_URL = "sqlite:///./sql_app.db"
        elif "postgresql" in self.DATABASE_URL:
            url = self.DATABASE_URL
            if "postgresql+asyncpg://" in url:
                url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            elif "postgresql://" in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            self.SYNC_DATABASE_URL = url


settings = Settings()
