"""
Talent Rediscovery API endpoint — scan candidate database and cross-reference
past profiles against a new job description using AI semantic match scoring.
"""
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.job import Job
from app.services.scoring_engine_service import ScoringEngineService

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class RediscoverRequest(BaseModel):
    job_id: uuid.UUID
    min_match_score: Optional[float] = Field(70.0, ge=0.0, le=100.0)


class RediscoverCandidateOut(BaseModel):
    candidate_id: uuid.UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    total_experience_years: float
    original_match_score: float
    new_match_score: float
    reasoning: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/rediscover",
    response_model=List[RediscoverCandidateOut],
    status_code=status.HTTP_200_OK,
    summary="Rediscover past candidates matching a new Job Description",
)
async def rediscover_talent(
    body: RediscoverRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Load active job details
    job_result = await db.execute(
        select(Job).where(Job.id == body.job_id, Job.company_id == current_user.company_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=body.job_id)

    # 2. Query all candidates inside company tenant
    cands_result = await db.execute(
        select(Candidate)
        .where(Candidate.company_id == current_user.company_id)
    )
    candidates = cands_result.scalars().all()
    results = []

    for c in candidates:
        # Load candidate resumes
        res_res = await db.execute(
            select(Resume).where(Resume.candidate_id == c.id)
        )
        resumes = res_res.scalars().all()
        if not resumes:
            continue
        primary_resume = resumes[0]

        # Skip candidates already linked to this job posting
        if primary_resume.job_id == body.job_id:
            continue

        # Score against the new Job Posting
        breakdown = await ScoringEngineService.evaluate_candidate(job, primary_resume)
        
        if breakdown.overall_score >= body.min_match_score:
            results.append(
                RediscoverCandidateOut(
                    candidate_id=c.id,
                    full_name=c.full_name,
                    email=c.email,
                    phone=c.phone,
                    location=c.location,
                    total_experience_years=c.total_experience_years or 0.0,
                    original_match_score=0.0,  # placeholder
                    new_match_score=breakdown.overall_score,
                    reasoning=breakdown.match_summary
                )
            )

    results.sort(key=lambda r: r.new_match_score, reverse=True)
    return results
