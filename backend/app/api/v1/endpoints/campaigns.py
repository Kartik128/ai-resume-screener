import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.campaign import CampaignTemplate

router = APIRouter()

class CampaignTemplateCreate(BaseModel):
    trigger_stage: str = Field(..., max_length=50)
    channel: str = Field(..., max_length=20)
    subject: Optional[str] = Field(None, max_length=255)
    body: str = Field(..., max_length=5000)
    is_active: bool = True

class CampaignTemplateOut(BaseModel):
    id: uuid.UUID
    trigger_stage: str
    channel: str
    subject: Optional[str]
    body: str
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CampaignTemplateOut])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(CampaignTemplate)
        .where(CampaignTemplate.company_id == current_user.company_id)
        .order_by(CampaignTemplate.created_at.desc())
    )
    return res.scalars().all()

@router.post("/", response_model=CampaignTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: CampaignTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_tmpl = CampaignTemplate(
        company_id=current_user.company_id,
        trigger_stage=body.trigger_stage.lower(),
        channel=body.channel.lower(),
        subject=body.subject,
        body=body.body,
        is_active=body.is_active,
    )
    db.add(new_tmpl)
    await db.commit()
    await db.refresh(new_tmpl)
    return new_tmpl

@router.delete("/{tmpl_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    tmpl_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(CampaignTemplate)
        .where(CampaignTemplate.id == tmpl_id)
        .where(CampaignTemplate.company_id == current_user.company_id)
    )
    await db.commit()
    return None
