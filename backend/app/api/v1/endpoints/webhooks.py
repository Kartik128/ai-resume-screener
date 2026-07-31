"""
Webhooks API endpoints — register integrations subscription urls, listing, and deletions.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, Field, HttpUrl

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.webhook import WebhookSubscription

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class WebhookCreate(BaseModel):
    target_url: str = Field(..., max_length=2000, description="Target callback URL to receive POST events")
    event_type: str = Field("candidate.stage_changed", max_length=50)


class WebhookOut(BaseModel):
    id: uuid.UUID
    target_url: str
    event_type: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=WebhookOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new integration webhook endpoint",
)
async def register_webhook(
    body: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = WebhookSubscription(
        company_id=current_user.company_id,
        target_url=body.target_url,
        event_type=body.event_type
    )
    db.add(sub)
    await db.commit()
    return WebhookOut(id=sub.id, target_url=sub.target_url, event_type=sub.event_type)


@router.get(
    "/",
    response_model=List[WebhookOut],
    summary="List all registered webhooks subscriptions for the company",
)
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.company_id == current_user.company_id)
    )
    subs = res.scalars().all()
    return [WebhookOut(id=s.id, target_url=s.target_url, event_type=s.event_type) for s in subs]


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete / unsubscribe integration webhook endpoint",
)
async def unsubscribe_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify owner
    res = await db.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.id == webhook_id, WebhookSubscription.company_id == current_user.company_id)
    )
    sub = res.scalar_one_or_none()
    if not sub:
        raise NotFoundException(resource="Webhook Subscription", identifier=webhook_id)

    await db.execute(delete(WebhookSubscription).where(WebhookSubscription.id == webhook_id))
    await db.commit()
    return {"success": True, "detail": "Webhook unsubscribed successfully"}


# ── Webhook Dispatch Utility ──────────────────────────────────────────────────

async def trigger_stage_changed_webhook(company_id: uuid.UUID, payload: dict, db: AsyncSession):
    """Utility function to simulate triggering post requests to external subscribers."""
    res = await db.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.company_id == company_id, WebhookSubscription.event_type == "candidate.stage_changed")
    )
    subs = res.scalars().all()
    for s in subs:
        # Log mock dispatch (in production: schedule celery / async requests client POST task)
        from loguru import logger
        logger.info(f"⚡ Dispatching Webhook (candidate.stage_changed) to {s.target_url} | Payload: {payload}")
