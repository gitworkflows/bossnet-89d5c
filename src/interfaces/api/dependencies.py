from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.entities.user import User
from infrastructure.persistence.sqlalchemy.database import get_db
from application.services.auth_service import AuthService
from application.services.user_service import UserService
from infrastructure.persistence.sqlalchemy.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    auto_error=False
)

# Dependency to get database session
async def get_db_session() -> Generator[AsyncSession, None, None]:
    """Get database session."""
    async with get_db() as session:
        try:
            yield session
        finally:
            await session.close()

# Dependency to get user repository
def get_user_repository(
    db: AsyncSession = Depends(get_db_session)
) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)

# Dependency to get user service
def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service."""
    return UserService(repository)

# Dependency to get auth service
def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get auth service."""
    return AuthService(user_repository)

# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user from token."""
    if not token:
        return None
        
    user = await auth_service.get_current_user(token)
    if not user:
        return None
        
    return user

# Dependency to require authentication
def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user or raise 401 if not authenticated."""
    if not current_user or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# Dependency to require admin role
def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user or raise 403 if not admin."""
    from core.entities.user import UserRole
    
    if UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
