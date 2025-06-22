from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from core.entities.user import User, UserRole, UserStatus
from core.value_objects.email import Email
from infrastructure.persistence.sqlalchemy.models.user import UserModel, UserRoleModel
from infrastructure.persistence.sqlalchemy.repositories.base import SQLAlchemyRepository

class UserRepository(SQLAlchemyRepository[UserModel, User]):
    """SQLAlchemy implementation of UserRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(session, UserModel, User)
        
    def _to_entity(self, model: Optional[UserModel]) -> Optional[User]:
        """Convert SQLAlchemy model to domain entity."""
        if model is None:
            return None
            
        return User(
            id=model.id,
            email=Email.create(model.email),
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            _password=model.password_hash,  # This will be handled by the Password value object
            is_active=model.is_active,
            is_verified=model.is_verified,
            status=UserStatus(model.status) if model.status else UserStatus.PENDING_VERIFICATION,
            roles=[UserRole(role) for role in model.roles],
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=model.last_login
        )
        
    def _to_model(self, entity: User) -> UserModel:
        """Convert domain entity to SQLAlchemy model."""
        if entity is None:
            return None
            
        model = UserModel(
            id=entity.id,
            email=str(entity.email) if entity.email else None,
            username=entity.username,
            first_name=entity.first_name,
            last_name=entity.last_name,
            password_hash=entity.password,  # This is the hashed password
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            roles=[UserRoleModel(user_id=entity.id, role=role.value) for role in entity.roles]
        )
    
    async def get_by_id(self, id: int) -> Optional[User]:
        """Get a user by ID."""
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == id)
        )
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._to_entity(user_model)
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination."""
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        user_models = result.scalars().all()
        return [self._to_entity(model) for model in user_models]
    
    async def add(self, entity: User) -> User:
        """Add a new user."""
        user_model = self._to_model(entity)
        self.session.add(user_model)
        await self.session.flush()
        
        # Update the entity with the generated ID
        entity.id = user_model.id
        
        # Clear any domain events after they've been handled
        entity.clear_events()
        
        return entity
    
    async def update(self, id: int, entity: User) -> Optional[User]:
        """Update an existing user."""
        # First get the existing user
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == id)
        )
        result = await self.session.execute(stmt)
        existing_model = result.scalar_one_or_none()
        
        if not existing_model:
            return None
            
        # Update the model with entity data
        updated_model = self._to_model(entity)
        
        # Copy the updated values to the existing model
        for key, value in updated_model.__dict__.items():
            if not key.startswith('_') and key != 'id' and key != 'roles':
                setattr(existing_model, key, value)
        
        # Handle roles update
        if hasattr(updated_model, 'roles'):
            # Remove existing roles
            existing_roles = set((r.role for r in existing_model.roles))
            updated_roles = set((r.role for r in updated_model.roles))
            
            # Add new roles
            for role in updated_roles - existing_roles:
                existing_model.roles.append(UserRoleModel(user_id=id, role=role))
            
            # Remove old roles
            for role in existing_roles - updated_roles:
                existing_model.roles = [r for r in existing_model.roles if r.role != role]
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by_field("email", email, options=[selectinload(UserModel.roles_rel)])
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by_field("username", username, options=[selectinload(UserModel.roles_rel)])
    
    async def get_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token."""
        # This would need to be implemented with a proper token verification
        # For now, we'll just return None
        return None
    
    async def email_exists(self, email: str, exclude_id: Optional[Union[int, str, UUID]] = None) -> bool:
        """Check if a user with the given email exists."""
        filters = [Filter(field="email", operator="eq", value=email)]
        if exclude_id is not None:
            filters.append(Filter(field="id", operator="ne", value=exclude_id))
        return await self.count(filters=filters) > 0
    
    async def username_exists(self, username: str, exclude_id: Optional[Union[int, str, UUID]] = None) -> bool:
        """Check if a user with the given username exists."""
        filters = [Filter(field="username", operator="eq", value=username)]
        if exclude_id is not None:
            filters.append(Filter(field="id", operator="ne", value=exclude_id))
        return await self.count(filters=filters) > 0
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        # Create the user model
        model = UserModel(
            email=str(user.email),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            password_hash=user.password,
            is_active=user.is_active,
            is_verified=user.is_verified,
            status=user.status.value if user.status else UserStatus.PENDING_VERIFICATION.value,
            roles=[role.value for role in user.roles] if user.roles else [UserRole.STUDENT.value]
        )
        
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        
        # Return the created user entity
        return await self.get_by_id(model.id)
    
    async def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        # Get existing user
        existing = await self.get_by_id(user.id)
        if not existing:
            return None
            
        # Update the user
        update_data = user.model_dump(
            exclude_unset=True,
            exclude={"id", "created_at", "updated_at", "last_login"}
        )
        
        # Handle email update
        if "email" in update_data and update_data["email"]:
            update_data["email"] = str(update_data["email"])
            
        # Handle status update
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
            
        # Handle roles update
        if "roles" in update_data and update_data["roles"]:
            # Convert roles to strings
            update_data["roles"] = [role.value for role in update_data["roles"]]
            
        # Update the user
        updated = await super().update(user.id, update_data)
        if not updated:
            return None
            
        return await self.get_by_id(user.id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by_field("email", email, options=[selectinload(UserModel.roles)])
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by_field("username", username, options=[selectinload(UserModel.roles)])
    
    async def get_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token."""
        # This would need to be implemented with a proper token verification
        # For now, we'll just return None
        return None
    
    async def email_exists(self, email: str, exclude_id: Optional[Union[int, str, UUID]] = None) -> bool:
        """Check if a user with the given email exists."""
        filters = [Filter(field="email", operator="eq", value=email)]
        if exclude_id is not None:
            filters.append(Filter(field="id", operator="ne", value=exclude_id))
        return await self.count(filters=filters) > 0
    
    async def username_exists(self, username: str, exclude_id: Optional[Union[int, str, UUID]] = None) -> bool:
        """Check if a user with the given username exists."""
        filters = [Filter(field="username", operator="eq", value=username)]
        if exclude_id is not None:
            filters.append(Filter(field="id", operator="ne", value=exclude_id))
        return await self.count(filters=filters) > 0
    
    async def add_role(self, user_id: Union[int, str, UUID], role: UserRole) -> bool:
        """Add a role to a user."""
        # Get user with roles
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        # Check if user already has the role
        if any(r.role == role.value for r in user.roles):
            return False
            
        # Add role to user
        user.roles.append(UserRoleModel(role=role.value))
        await self.session.flush()
        return True
    
    async def remove_role(self, user_id: Union[int, str, UUID], role: UserRole) -> bool:
        """Remove a role from a user."""
        # Get user with roles
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.roles))
            .where(UserModel.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        # Find and remove role
        role_to_remove = next(
            (r for r in user.roles if r.role == role.value),
            None
        )
        
        if not role_to_remove:
            return False
            
        user.roles.remove(role_to_remove)
        await self.session.flush()
        return True
    
    async def update_status(self, user_id: Union[int, str, UUID], status: UserStatus) -> bool:
        """Update a user's status."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(status=status.value)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def update_last_login(self, id: Union[int, str, UUID]) -> None:
        """Update the last login timestamp for a user."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(last_login=datetime.utcnow())
        )
        await self.session.execute(stmt)
    
    async def update_password(self, id: Union[int, str, UUID], hashed_password: str) -> None:
        """Update a user's password."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(password_hash=hashed_password)
        )
        await self.session.execute(stmt)
    
    async def verify_email(self, id: Union[int, str, UUID]) -> None:
        """Mark a user's email as verified."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(
                is_verified=True, 
                status=UserStatus.ACTIVE.value, 
                email_verified_at=datetime.utcnow()
            )
        )
        await self.session.execute(stmt)
    
    async def exists(self, **filters) -> bool:
        """Check if a user exists with the given filters."""
        if not filters:
            return False
                
        conditions = []
        for field, value in filters.items():
            if hasattr(UserModel, field):
                conditions.append(getattr(UserModel, field) == value)
            
        if not conditions:
            return False
                
        stmt = select(func.count()).select_from(UserModel).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
