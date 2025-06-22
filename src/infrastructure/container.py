from typing import Dict, Type, Any, Optional
from functools import lru_cache

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.repositories.base import UserRepository
from core.services.auth_service import AuthService
from infrastructure.auth.jwt_service import JWTService
from infrastructure.persistence.user_repository import UserRepository as UserRepositoryImpl

class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._overrides: Dict[Type, Type] = {}
    
    def wire(self, modules=None):
        """Wire the container with modules."""
        # This would be used to wire the container with FastAPI or other frameworks
        pass
    
    def register(self, interface: Type, implementation: Any):
        """Register an implementation for an interface."""
        self._instances[interface] = implementation
    
    def resolve(self, interface: Type) -> Any:
        """Resolve an implementation for an interface."""
        if interface in self._overrides:
            return self._overrides[interface]
        
        if interface in self._instances:
            return self._instances[interface]
        
        # Auto-wire common dependencies
        if interface == UserRepository:
            return self.user_repository()
        elif interface == AuthService:
            return self.auth_service()
        
        raise ValueError(f"No implementation found for {interface.__name__}")
    
    # Database
    @lru_cache
    def get_db_engine(self):
        """Get the database engine."""
        from config import settings
        return create_async_engine(settings.DATABASE_URL)
    
    @lru_cache
    def get_db_session_factory(self):
        """Get the database session factory."""
        return sessionmaker(
            self.get_db_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
    
    async def get_db_session(self) -> AsyncSession:
        """Get a database session."""
        session_factory = self.get_db_session_factory()
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # Repositories
    @lru_cache
    def user_repository(self) -> UserRepository:
        """Get the user repository."""
        # This is a simple implementation - in a real app, you'd get the session from the request
        # and create a new repository instance per request
        return UserRepositoryImpl(self.get_db_session())
    
    # Services
    @lru_cache
    def auth_service(self) -> AuthService:
        """Get the auth service."""
        return JWTService(self.resolve(UserRepository))

# Create a global container instance
container = Container()
