from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class StudentBase(BaseModel):
    student_id: str = Field(..., description="Unique identifier for the student")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: date
    gender: Gender
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    division: Optional[str] = None
    postal_code: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": "STU20230001",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "2005-01-15",
                "gender": "male",
                "email": "john.doe@example.com",
                "phone": "+8801712345678",
                "address": "123 Main Road",
                "city": "Dhaka",
                "district": "Dhaka",
                "division": "Dhaka",
                "postal_code": "1207"
            }
        }

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    division: Optional[str] = None
    postal_code: Optional[str] = None

class StudentInDB(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class StudentResponse(StudentInDB):
    pass

class PaginatedStudentResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[StudentResponse]
