import os
from functools import lru_cache
from typing import List, Optional, Dict, Any, Union, Literal

from pydantic import AnyHttpUrl, PostgresDsn, validator, field_validator, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "Bangladesh Education Data API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "False").lower() in ("true", "1", "t")
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "student_data_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # SQLAlchemy
    SQL_ECHO: bool = DEBUG
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Testing
    TESTING: bool = os.getenv("TESTING", "False").lower() in ("true", "1", "t")
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_student_data_db"
    )
    
    # Security Headers
    SECURITY_HEADERS: Dict[str, Any] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # First superuser
    FIRST_SUPERUSER_EMAIL: str = os.getenv("FIRST_SUPERUSER_EMAIL", "admin@example.com")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")
    
    # Computed properties
    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Validators
    @field_validator("CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        v = v.upper()
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return v
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'  # Ignore extra environment variables
    )

# Create settings instance
settings = Settings()

# For dependency injection
def get_settings() -> Settings:
    return settings
