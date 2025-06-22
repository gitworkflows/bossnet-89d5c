from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.entities.user import User
from core.services.auth_service import AuthService, TokenPair, AuthenticationError, InvalidCredentialsError, AccountLockedError
from core.repositories.base import UserRepository

# Configuration (should be moved to settings)
SECRET_KEY = "your-secret-key-here"  # Use environment variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class JWTService(AuthService):
    """JWT-based authentication service implementation."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user with username and password."""
        user = await self.user_repository.get_by_username(username)
        if not user:
            # Hash a dummy password to prevent timing attacks
            self.pwd_context.hash("dummy_password")
            raise InvalidCredentialsError("Incorrect username or password")
        
        if not self.pwd_context.verify(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect username or password")
        
        if not user.is_active:
            raise AccountLockedError("Account is inactive")
        
        # Update last login timestamp
        await self.user_repository.update_last_login(user.id)
        
        return user
    
    def _create_token(self, subject: str, expires_delta: timedelta) -> str:
        """Create a JWT token."""
        expire = datetime.utcnow() + expires_delta
        to_encode = {"sub": str(subject), "exp": expire}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    async def create_tokens(self, user_id: int) -> TokenPair:
        """Create access and refresh tokens for a user."""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = self._create_token(
            subject=user_id,
            expires_delta=access_token_expires
        )
        
        refresh_token = self._create_token(
            subject=user_id,
            expires_delta=refresh_token_expires
        )
        
        # Store refresh token in database (implementation needed)
        # await self._store_refresh_token(user_id, refresh_token)
        
        return TokenPair((access_token, refresh_token))
    
    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Create a new access token using a refresh token."""
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload.get("sub"))
            
            # Verify the refresh token is valid and not revoked
            # if not await self._is_valid_refresh_token(user_id, refresh_token):
            #     raise InvalidCredentialsError("Invalid refresh token")
            
            # Create new tokens
            return await self.create_tokens(user_id)
            
        except JWTError:
            raise InvalidCredentialsError("Invalid refresh token")
    
    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke a refresh token."""
        # Implementation needed to mark token as revoked
        pass
    
    async def get_current_user(self, token: str) -> User:
        """Get the current user from an access token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload.get("sub"))
            
            if user_id is None:
                raise InvalidCredentialsError("Could not validate credentials")
                
            user = await self.user_repository.get_by_id(user_id)
            if user is None:
                raise InvalidCredentialsError("User not found")
                
            return user
            
        except JWTError:
            raise InvalidCredentialsError("Could not validate credentials")
    
    async def register_user(self, user_data) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
            
        existing_user = await self.user_repository.get_by_username(user_data.username)
        if existing_user:
            raise ValueError("Username already taken")
        
        # Hash the password
        hashed_password = self.pwd_context.hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            roles=["student"]  # Default role
        )
        
        # Save user to database
        created_user = await self.user_repository.add(user)
        
        # Send verification email (implementation needed)
        # await self._send_verification_email(created_user)
        
        return created_user
    
    async def verify_email(self, token: str) -> bool:
        """Verify a user's email using a verification token."""
        # Implementation needed
        pass
    
    async def request_password_reset(self, email: str) -> None:
        """Request a password reset for a user."""
        # Implementation needed
        pass
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset a user's password using a reset token."""
        # Implementation needed
        pass
