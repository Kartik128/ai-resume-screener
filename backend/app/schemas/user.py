import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole
from app.schemas.company import CompanyRead


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)
    role: UserRole = UserRole.RECRUITER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    company_id: uuid.UUID


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    company_id: uuid.UUID
    company: Optional[CompanyRead] = None
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
