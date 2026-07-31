"""
Candidate Experience Feedback API router. Submit NPS scores and reviews from public candidate portals.
"""
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.feedback import CandidateExperienceFeedback

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class FeedbackSubmitRequest(BaseModel):
    candidate_id: uuid.UUID
    nps_score: int = Field(..., ge=0, le=10, description="Net Promoter Score between 0 and 10")
    feedback_text: str = Field(None, max_length=2000)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Submit candidate experience feedback review (NPS score) from public portals",
)
async def submit_candidate_feedback(
    body: FeedbackSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    feed = CandidateExperienceFeedback(
        candidate_id=body.candidate_id,
        nps_score=body.nps_score,
        feedback_text=body.feedback_text
    )
    db.add(feed)
    await db.commit()
    return {"success": True, "detail": "Feedback saved successfully"}


from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models.candidate import Candidate
from app.api.deps import get_current_user
from app.models.user import User

@router.get(
    "/summary",
    summary="Retrieve aggregate Candidate Experience Net Promoter Score and details",
)
async def get_experience_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Query all candidate experience feedback matching current user's company_id context
    res = await db.execute(
        select(CandidateExperienceFeedback)
        .join(Candidate, CandidateExperienceFeedback.candidate_id == Candidate.id)
        .options(joinedload(CandidateExperienceFeedback.candidate))
        .where(Candidate.company_id == current_user.company_id)
    )
    feedback_entries = res.scalars().all()

    total = len(feedback_entries)
    if total == 0:
        return {
            "nps_score": 0,
            "total_responses": 0,
            "promoters": 0,
            "passives": 0,
            "detractors": 0,
            "reviews": []
        }

    promoters = sum(1 for f in feedback_entries if f.nps_score >= 9)
    passives = sum(1 for f in feedback_entries if f.nps_score >= 7 and f.nps_score <= 8)
    detractors = sum(1 for f in feedback_entries if f.nps_score <= 6)
    
    nps = ((promoters - detractors) / total) * 100

    reviews = [
        {
            "id": str(f.id),
            "score": f.nps_score,
            "comment": f.feedback_text,
            "candidate_name": f.candidate.full_name,
            "submitted_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in feedback_entries
    ]

    return {
        "nps_score": round(nps, 1),
        "total_responses": total,
        "promoters": promoters,
        "passives": passives,
        "detractors": detractors,
        "reviews": reviews
    }
