"""
Offer Workflow API router — compose offer templates, release compensation packages, and track e-signatures.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.offer import OfferLetter
from app.models.application import Application, ApplicationStatus
from app.models.pipeline_activity import PipelineActivity, ActivityType

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class OfferReleaseRequest(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    base_salary: float = Field(..., gt=0)
    equity_grants: Optional[str] = None


class OfferOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    base_salary: float
    equity_grants: Optional[str]
    sign_status: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/release",
    response_model=OfferOut,
    status_code=status.HTTP_201_CREATED,
    summary="Release and send a formal compensation offer letter package to a candidate",
)
async def release_offer_letter(
    body: OfferReleaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Locate matching application to transition status
    app_res = await db.execute(
        select(Application).where(Application.candidate_id == body.candidate_id, Application.job_id == body.job_id)
    )
    app = app_res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="No active application found for this candidate and job pairing.")

    # Save Offer
    offer = OfferLetter(
        candidate_id=body.candidate_id,
        job_id=body.job_id,
        base_salary=body.base_salary,
        equity_grants=body.equity_grants,
        sign_status="sent"
    )
    db.add(offer)

    # Transition application status to offer released
    old_status = app.status
    app.status = ApplicationStatus.OFFER_RELEASED

    # Write timeline logs
    act = PipelineActivity(
        application_id=app.id,
        activity_type=ActivityType.STAGE_CHANGE,
        from_value=old_status.value,
        to_value=ApplicationStatus.OFFER_RELEASED.value,
        note=f"✍️ Compensation Offer released: Base Salary: ${body.base_salary:,.2f} | Equity: {body.equity_grants or 'None'}",
    )
    db.add(act)
    await db.commit()

    return OfferOut(
        id=offer.id,
        candidate_id=offer.candidate_id,
        job_id=offer.job_id,
        base_salary=offer.base_salary,
        equity_grants=offer.equity_grants,
        sign_status=offer.sign_status
    )


@router.get(
    "/candidate/{candidate_id}",
    response_model=Optional[OfferOut],
    summary="Get active compensation offer details for a specific candidate",
)
async def get_candidate_offer(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(OfferLetter).where(OfferLetter.candidate_id == candidate_id)
    )
    offer = res.scalar_one_or_none()
    if not offer:
        return None

    return OfferOut(
        id=offer.id,
        candidate_id=offer.candidate_id,
        job_id=offer.job_id,
        base_salary=offer.base_salary,
        equity_grants=offer.equity_grants,
        sign_status=offer.sign_status
    )
