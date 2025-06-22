from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Enum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

# Association table for many-to-many relationship between User and Role
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
)

class Role(BaseModel):
    """Role model for storing user roles."""
    __tablename__ = 'roles'
    
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationship
    users: Mapped[List['User']] = relationship(
        'User', secondary=user_roles, back_populates='roles'
    )

class User(BaseModel):
    """User model for storing user related details."""
    __tablename__ = 'users'
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    roles: Mapped[List[Role]] = relationship(
        'Role', secondary=user_roles, back_populates='users', lazy='selectin'
    )
    
    # Indexes
    __table_args__ = (
        # Add any additional table arguments here
    )
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has the specified role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(self.has_role(role_name) for role_name in role_names)
    
    def has_all_roles(self, role_names: List[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(self.has_role(role_name) for role_name in role_names)

class RefreshToken(BaseModel):
    """Refresh token model for JWT token refreshing."""
    __tablename__ = 'refresh_tokens'
    
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationship
    user: Mapped['User'] = relationship('User', back_populates='refresh_tokens')

# Add the back-reference after both classes are defined
User.refresh_tokens = relationship('RefreshToken', back_populates='user', lazy='dynamic')
