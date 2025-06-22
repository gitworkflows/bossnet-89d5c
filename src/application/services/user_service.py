from typing import List, Optional
from datetime import datetime

from core.entities.user import User, UserCreate, UserUpdate, UserRole
from core.repositories.base import Repository
from core.services.base_service import BaseService
from core.domain.events import event_bus, UserRegistered, UserEmailVerified, UserPasswordChanged

class UserService(BaseService[User, int]):
    """Service for user management operations."""
    
    def __init__(self, repository: Repository[User, int]):
        """Initialize with a user repository."""
        super().__init__(repository)
    
    async def register_user(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str
    ) -> User:
        """Register a new user."""
        # Check if email or username is already taken
        if await self._is_email_taken(email):
            raise ValueError("Email is already registered")
            
        if await self._is_username_taken(username):
            raise ValueError("Username is already taken")
        
        # Create and save the user
        user = User.register(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        
        # Save the user to the database
        saved_user = await self.repository.add(user)
        
        # Publish domain events
        for event in saved_user.events:
            event_bus.publish(event)
        
        return saved_user
    
    async def verify_email(self, user_id: int) -> Optional[User]:
        """Verify a user's email address."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
            
        user.verify_email()
        updated_user = await self.repository.update(user_id, user)
        
        # Publish domain events
        for event in updated_user.events:
            event_bus.publish(event)
            
        return updated_user
    
    async def change_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change a user's password."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
            
        # Verify current password
        if not user.verify_password(current_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.change_password(new_password)
        await self.repository.update(user_id, user)
        
        # Publish domain events
        for event in user.events:
            event_bus.publish(event)
            
        return True
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        # This is a simplified version - in a real app, you'd want to handle this differently
        user = await self.repository.get_by_username(username)
        if user and user.verify_password(password) and user.is_active:
            return user
        return None
    
    async def _is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if an email is already taken."""
        if hasattr(self.repository, 'is_email_taken'):
            return await self.repository.is_email_taken(email, exclude_user_id)
        
        # Fallback implementation
        user = await self.repository.get_by_email(email)
        if not user:
            return False
        return user.id != exclude_user_id if exclude_user_id else True
    
    async def _is_username_taken(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if a username is already taken."""
        if hasattr(self.repository, 'is_username_taken'):
            return await self.repository.is_username_taken(username, exclude_user_id)
        
        # Fallback implementation
        user = await self.repository.get_by_username(username)
        if not user:
            return False
        return user.id != exclude_user_id if exclude_user_id else True

    def _create_entity_from_data(self, data: dict) -> User:
        """Create a user entity from dictionary data."""
        return User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            _password=data['password'],
            is_active=data.get('is_active', True),
            is_verified=data.get('is_verified', False),
            roles=data.get('roles', [UserRole.STUDENT])
        )
