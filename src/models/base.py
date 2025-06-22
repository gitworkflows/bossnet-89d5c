from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import as_declared, declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

T = TypeVar("T", bound="BaseModel")

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        ""
        Generate __tablename__ automatically.
        Converts CamelCase class name to snake_case table name.
        """
        return ''.join(['_'+c.lower() if c.isupper() else c for c in cls.__name__]).lstrip('_')


class BaseModel(Base):
    """Base model that includes common columns and methods."""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns  # type: ignore
        }
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create model instance from dictionary."""
        return cls(**data)  # type: ignore
    
    def update(self, **kwargs) -> None:
        """Update model instance with given attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
