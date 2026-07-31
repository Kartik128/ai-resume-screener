import uuid
from datetime import datetime
from typing import Any, Optional
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


def user_to_read_schema(user: Any) -> UserRead:
    company_schema = None
    try:
        if hasattr(user, "company") and user.company:
            c = user.company
            company_schema = CompanyRead(
                id=c.id,
                name=c.name,
                slug=c.slug,
                domain=getattr(c, "domain", None),
                subscription_plan=getattr(c, "subscription_plan", SubscriptionPlan.STARTER),
                is_active=getattr(c, "is_active", True),
            )
    except Exception:
        company_schema = None

    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        company_id=user.company_id,
        company=company_schema,
        last_login_at=getattr(user, "last_login_at", None),
        created_at=getattr(user, "created_at", None),
        updated_at=getattr(user, "updated_at", None),
    )
