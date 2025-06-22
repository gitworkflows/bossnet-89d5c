from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from core.config import settings
from core.entities.user import User, UserCreate, UserInDB
from application.services.auth_service import AuthService
from application.services.user_service import UserService
from interfaces.api.dependencies import get_auth_service, get_user_service
from interfaces.api.v1.schemas.token import Token, TokenPayload

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": auth_service.create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Test access token."""
    return current_user

@router.post("/register", response_model=User)
async def register_user(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Register new user."""
    try:
        user = await user_service.register_user(
            email=user_in.email,
            username=user_in.username,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            password=user_in.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/password-recovery/{email}", response_model=Dict[str, str])
async def recover_password(
    email: EmailStr,
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Password Recovery."""
    # TODO: Implement password recovery
    return {"msg": "Password recovery email sent"}

@router.post("/reset-password/", response_model=Dict[str, str])
async def reset_password(
    token: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Reset password."""
    # TODO: Implement password reset
    return {"msg": "Password updated successfully"}
