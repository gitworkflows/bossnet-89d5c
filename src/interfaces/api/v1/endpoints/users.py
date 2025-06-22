from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from core.entities.user import User, UserCreate, UserUpdate, UserInDB
from application.services.user_service import UserService
from interfaces.api.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_user_service
)

router = APIRouter()

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Retrieve users."""
    users = await user_service.list(skip=skip, limit=limit)
    return users

@router.post("/", response_model=User)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Create new user."""
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

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user."""
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Update own user."""
    # Only update fields that are provided
    update_data = user_in.dict(exclude_unset=True)
    
    # Remove password from update data if present
    update_data.pop("password", None)
    
    # Update the user
    user = await user_service.update(current_user.id, update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.get("/{user_id}", response_model=User)
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Get a specific user by id."""
    # Regular users can only see their own profile
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Update a user."""
    # Only admins can update other users
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Only admins can update roles and active status
    if not current_user.is_superuser:
        if "is_active" in user_in.dict(exclude_unset=True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update active status",
            )
        if "roles" in user_in.dict(exclude_unset=True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update roles",
            )
    
    user = await user_service.update(user_id, user_in.dict(exclude_unset=True))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    """Delete a user."""
    # Prevent users from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    await user_service.delete(user_id)
    return user
