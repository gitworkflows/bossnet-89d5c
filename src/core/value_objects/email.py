from pydantic import EmailStr, validator
from typing import Optional

class Email(EmailStr):
    """Value object representing an email address with validation."""
    
    @classmethod
    def create(cls, email: str) -> 'Email':
        """Factory method to create an Email value object."""
        return cls(email)
    
    def __repr__(self) -> str:
        return f'Email({super().__str__()})'
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return str(self) == str(other)
    
    def __hash__(self) -> int:
        return hash(str(self))
