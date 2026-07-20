import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.company import SubscriptionPlan


class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255, description="Company Name")
    slug: str = Field(..., max_length=255, description="Unique Company Slug")
    domain: Optional[str] = Field(None, max_length=255)
    subscription_plan: SubscriptionPlan = SubscriptionPlan.STARTER


class CompanyCreate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    id: uuid.UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
