from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings
from core.entities.user import User
from core.domain.events import event_bus, UserRegistered, UserEmailVerified
from core.repositories.base import Repository

class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self, user_repository: Repository[User, int]):
        """Initialize with a user repository."""
        self.user_repository = user_repository
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate a password hash."""
        return self.pwd_context.hash(password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/email and password."""
        # Try to find user by username or email
        user = await self.user_repository.get_by_username(username)
        if not user:
            user = await self.user_repository.get_by_email(username)
        
        if not user or not self.verify_password(password, user.password):
            return None
            
        if not user.is_active:
            return None
            
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.REFRESH_SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    def verify_token(self, token: str, is_refresh: bool = False) -> Optional[dict]:
        """Verify a JWT token."""
        try:
            secret_key = settings.REFRESH_SECRET_KEY if is_refresh else settings.SECRET_KEY
            payload = jwt.decode(
                token, 
                secret_key, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a JWT token."""
        payload = self.verify_token(token)
        if not payload:
            return None
            
        username = payload.get("sub")
        if not username:
            return None
            
        user = await self.user_repository.get_by_username(username)
        if not user or not user.is_active:
            return None
            
        return user
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh an access token using a refresh token."""
        payload = self.verify_token(refresh_token, is_refresh=True)
        if not payload or payload.get("type") != "refresh":
            return None
            
        username = payload.get("sub")
        if not username:
            return None
            
        user = await self.user_repository.get_by_username(username)
        if not user or not user.is_active:
            return None
            
        # Create new access token
        access_token = self.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return access_token
