from datetime import datetime
from typing import List, Optional, Set
from enum import Enum
from pydantic import EmailStr, Field, validator

from .base import Entity


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STAFF = "staff"
    STUDENT = "student"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending_verification"


class User(Entity):
    """User domain model representing a system user."""
    
    email: EmailStr = Field(..., description="User's email address (must be unique)")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password_hash: str = Field(..., description="Hashed password")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    roles: Set[UserRole] = Field(
        default={UserRole.STUDENT}, 
        description="Set of user roles"
    )
    status: UserStatus = Field(
        default=UserStatus.PENDING,
        description="Account status"
    )
    email_verified: bool = Field(
        default=False,
        description="Whether the email has been verified"
    )
    last_login: Optional[datetime] = Field(
        default=None,
        description="Last login timestamp"
    )
    
    # Validators
    @validator('username')
    def username_must_be_valid(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()
    
    @validator('full_name')
    def full_name_must_be_valid(cls, v):
        # Ensure full name contains at least first and last name
        names = v.strip().split()
        if len(names) < 2:
            raise ValueError('Full name must include first and last name')
        return ' '.join(name.strip().title() for name in names)
    
    # Domain methods
    def has_role(self, role: UserRole) -> bool:
        """Check if user has the specified role."""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return UserRole.ADMIN in self.roles
    
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE
    
    def verify_password(self, password: str, hasher) -> bool:
        """Verify if the provided password matches the stored hash."""
        return hasher.verify(password, self.password_hash)
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def add_role(self, role: UserRole) -> None:
        """Add a role to the user."""
        self.roles.add(role)
    
    def remove_role(self, role: UserRole) -> None:
        """Remove a role from the user."""
        if role in self.roles:
            self.roles.remove(role)
    
    def mark_email_verified(self) -> None:
        """Mark the user's email as verified."""
        self.email_verified = True
        if self.status == UserStatus.PENDING:
            self.status = UserStatus.ACTIVE


class TokenPayload(Entity):
    """Token payload domain model for JWT tokens."""
    
    sub: str = Field(..., description="Subject (usually user ID)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(default_factory=datetime.utcnow, description="Issued at")
    type: str = Field(..., description="Token type (e.g., 'access', 'refresh')")
    scopes: List[str] = Field(
        default_factory=list, 
        description="List of scopes/token permissions"
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.utcnow() > self.exp
