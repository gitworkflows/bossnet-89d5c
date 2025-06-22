"""
Security-related configuration settings.
"""
import os
from typing import List, Set
from pydantic import BaseSettings, validator

class SecuritySettings(BaseSettings):
    """Security-related settings."""
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    
    # Security headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
    
    # Rate limiting
    RATE_LIMIT: str = "100/minute"
    RATE_LIMIT_BYPASS_HEADER: str = "X-API-Key"
    
    # Request validation
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: Set[str] = {
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    # Security middleware
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_REQUEST_VALIDATION: bool = True
    ENABLE_HTTPS_REDIRECT: bool = not bool(os.getenv('DEBUG', 'false').lower() == 'true')
    
    # Allowed hosts (for production)
    ALLOWED_HOSTS: List[str] = ["*"] if os.getenv('DEBUG', 'false').lower() == 'true' else [
        "example.com",
        "api.example.com",
        "www.example.com"
    ]
    
    # Session security
    SESSION_COOKIE_SECURE: bool = not bool(os.getenv('DEBUG', 'false').lower() == 'true')
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # CSRF protection
    CSRF_COOKIE_SECURE: bool = not bool(os.getenv('DEBUG', 'false').lower() == 'true')
    CSRF_COOKIE_HTTPONLY: bool = True
    CSRF_TRUSTED_ORIGINS: List[str] = []
    
    # Security logging
    LOG_SENSITIVE_REQUESTS: bool = True
    LOG_BLOCKED_REQUESTS: bool = True
    
    @validator('CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "SECURITY_"

# Create security settings instance
security_settings = SecuritySettings()
