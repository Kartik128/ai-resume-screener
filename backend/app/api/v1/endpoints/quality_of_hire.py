"""
Quality-of-Hire Review API — post-hire 30/60/90-day manager feedback forms that close
the AI scoring loop and feed back into scorecard weight calibration.
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class QoHReviewRequest(BaseModel):
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    review_period: str = Field("30_day", pattern="^(30_day|60_day|90_day|180_day)$")
    performance_rating: int = Field(..., ge=1, le=10, description="Overall job performance rating 1-10")
    culture_fit_rating: int = Field(..., ge=1, le=10)
    skills_match_rating: int = Field(..., ge=1, le=10)
    retention_risk: str = Field("low", pattern="^(low|medium|high)$")
    notes: Optional[str] = Field(None, max_length=3000)


class QoHReviewOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    review_period: str
    performance_rating: int
    culture_fit_rating: int
    skills_match_rating: int
    retention_risk: str
    notes: Optional[str]
    composite_score: float


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/submit",
    response_model=QoHReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit post-hire quality-of-hire review for a hired candidate (30/60/90/180-day check-in)",
)
async def submit_qoh_review(
    body: QoHReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review_id = uuid.uuid4()
    composite = round((body.performance_rating + body.culture_fit_rating + body.skills_match_rating) / 3.0, 2)

    await db.execute(
        text("""
            INSERT INTO quality_of_hire_reviews
              (id, candidate_id, job_id, reviewer_id, review_period, performance_rating,
               culture_fit_rating, skills_match_rating, retention_risk, notes)
            VALUES (:id, :cid, :jid, :rid, :period, :perf, :culture, :skills, :risk, :notes)
        """),
        {
            "id": str(review_id),
            "cid": str(body.candidate_id),
            "jid": str(body.job_id),
            "rid": str(current_user.id),
            "period": body.review_period,
            "perf": body.performance_rating,
            "culture": body.culture_fit_rating,
            "skills": body.skills_match_rating,
            "risk": body.retention_risk,
            "notes": body.notes,
        }
    )
    await db.commit()

    return QoHReviewOut(
        id=review_id,
        candidate_id=body.candidate_id,
        job_id=body.job_id,
        review_period=body.review_period,
        performance_rating=body.performance_rating,
        culture_fit_rating=body.culture_fit_rating,
        skills_match_rating=body.skills_match_rating,
        retention_risk=body.retention_risk,
        notes=body.notes,
        composite_score=composite,
    )


@router.get(
    "/candidate/{candidate_id}",
    response_model=List[QoHReviewOut],
    summary="List all quality-of-hire check-in reviews for a specific hired candidate",
)
async def list_candidate_reviews(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        text("SELECT * FROM quality_of_hire_reviews WHERE candidate_id = :cid ORDER BY created_at DESC"),
        {"cid": str(candidate_id)}
    )
    rows = res.mappings().all()
    return [
        QoHReviewOut(
            id=uuid.UUID(r["id"]),
            candidate_id=uuid.UUID(r["candidate_id"]),
            job_id=uuid.UUID(r["job_id"]),
            review_period=r["review_period"],
            performance_rating=r["performance_rating"],
            culture_fit_rating=r["culture_fit_rating"],
            skills_match_rating=r["skills_match_rating"],
            retention_risk=r["retention_risk"],
            notes=r["notes"],
            composite_score=round((r["performance_rating"] + r["culture_fit_rating"] + r["skills_match_rating"]) / 3.0, 2),
        )
        for r in rows
    ]
