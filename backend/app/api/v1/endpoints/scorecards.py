"""
Scorecard endpoints — GET, PUT, and reset scoring dimension weights for a job.
"""
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, model_validator
from typing import Optional

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.scorecard import Scorecard
from app.repositories.job_repository import JobRepository

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "w_mandatory_skills": 40.0,
    "w_experience": 20.0,
    "w_nice_to_have": 10.0,
    "w_career_stability": 10.0,
    "w_industry_match": 8.0,
    "w_education": 5.0,
    "w_certifications": 4.0,
    "w_location": 3.0,
}


class ScorecardWeights(BaseModel):
    w_mandatory_skills: float = Field(40.0, ge=0.0, le=100.0, description="Mandatory Skills weight %")
    w_experience: float = Field(20.0, ge=0.0, le=100.0, description="Experience Depth weight %")
    w_nice_to_have: float = Field(10.0, ge=0.0, le=100.0, description="Nice-to-Have Skills weight %")
    w_career_stability: float = Field(10.0, ge=0.0, le=100.0, description="Career Stability weight %")
    w_industry_match: float = Field(8.0, ge=0.0, le=100.0, description="Industry Domain Match weight %")
    w_education: float = Field(5.0, ge=0.0, le=100.0, description="Education Fit weight %")
    w_certifications: float = Field(4.0, ge=0.0, le=100.0, description="Certifications weight %")
    w_location: float = Field(3.0, ge=0.0, le=100.0, description="Location weight %")
    criteria_notes: Optional[dict] = Field(None, description="Optional per-dimension custom notes")

    @model_validator(mode="after")
    def weights_sum_to_100(self):
        total = (
            self.w_mandatory_skills + self.w_experience + self.w_nice_to_have
            + self.w_career_stability + self.w_industry_match + self.w_education
            + self.w_certifications + self.w_location
        )
        if abs(total - 100.0) > 0.5:
            raise ValueError(f"All weights must sum to 100%. Current sum: {total:.1f}%")
        return self


class ScorecardResponse(ScorecardWeights):
    job_id: uuid.UUID
    is_custom: bool = True


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_default(job_id: uuid.UUID, db: AsyncSession) -> dict:
    result = await db.execute(select(Scorecard).where(Scorecard.job_id == job_id))
    sc = result.scalar_one_or_none()
    if sc:
        return {
            "job_id": job_id,
            "w_mandatory_skills": sc.w_mandatory_skills,
            "w_experience": sc.w_experience,
            "w_nice_to_have": sc.w_nice_to_have,
            "w_career_stability": sc.w_career_stability,
            "w_industry_match": sc.w_industry_match,
            "w_education": sc.w_education,
            "w_certifications": sc.w_certifications,
            "w_location": sc.w_location,
            "criteria_notes": sc.criteria_notes,
            "is_custom": True,
        }
    return {"job_id": job_id, **DEFAULT_WEIGHTS, "criteria_notes": None, "is_custom": False}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/{job_id}",
    summary="Get scoring weights for a job (returns defaults if not customised)",
)
async def get_scorecard(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job", identifier=job_id)
    return await _get_or_default(job_id, db)


async def _recalculate_candidate_scores(job, sc_weights, db: AsyncSession):
    from app.repositories.resume_repository import ResumeRepository
    from app.repositories.score_repository import ScoreRepository
    from app.services.scoring_engine_service import ScoringEngineService

    resume_repo = ResumeRepository(db)
    score_repo = ScoreRepository(db)

    custom_weights = None
    if sc_weights:
        custom_weights = {
            "mandatory_skills": sc_weights.w_mandatory_skills,
            "experience": sc_weights.w_experience,
            "nice_to_have": sc_weights.w_nice_to_have,
            "career_stability": sc_weights.w_career_stability,
            "industry_match": sc_weights.w_industry_match,
            "education": sc_weights.w_education,
            "certifications": sc_weights.w_certifications,
            "location": sc_weights.w_location,
        }

    resumes = await resume_repo.list_by_job(job.id)
    for res in resumes:
        breakdown = await ScoringEngineService.evaluate_candidate(job, res, custom_weights)
        await score_repo.save_or_update_score(
            job_id=job.id,
            candidate_id=res.candidate_id,
            resume_id=res.id,
            breakdown=breakdown,
        )


@router.put(
    "/{job_id}",
    summary="Save custom scoring weights for a job (weights must sum to 100%)",
)
async def save_scorecard(
    job_id: uuid.UUID,
    body: ScorecardWeights,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job", identifier=job_id)

    result = await db.execute(select(Scorecard).where(Scorecard.job_id == job_id))
    sc = result.scalar_one_or_none()

    if sc:
        for field, value in body.model_dump(exclude={"criteria_notes"}).items():
            setattr(sc, field, value)
        sc.criteria_notes = body.criteria_notes
    else:
        sc = Scorecard(
            job_id=job_id,
            created_by=current_user.id,
            **body.model_dump()
        )
        db.add(sc)

    await db.commit()
    
    # Trigger recalculation for all candidates of the job
    await _recalculate_candidate_scores(job, sc, db)
    await db.commit()

    return {"success": True, "job_id": str(job_id), "message": "Scorecard saved and candidate match scores updated successfully."}


@router.post(
    "/{job_id}/reset",
    summary="Reset scorecard to AI default weights",
)
async def reset_scorecard(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job", identifier=job_id)

    result = await db.execute(select(Scorecard).where(Scorecard.job_id == job_id))
    sc = result.scalar_one_or_none()
    if sc:
        await db.delete(sc)
        await db.commit()

    # Recalculate candidates back to default AI weights
    await _recalculate_candidate_scores(job, None, db)
    await db.commit()

    return {"success": True, "job_id": str(job_id), "message": "Scorecard reset to defaults and candidate match scores updated."}
