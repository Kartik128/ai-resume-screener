import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.score_repository import ScoreRepository
from app.schemas.scoring import RankedCandidateScore, ScoreBreakdownResponse
from app.services.scoring_engine_service import ScoringEngineService

router = APIRouter()


@router.post(
    "/evaluate/{job_id}/{candidate_id}",
    response_model=ScoreBreakdownResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate candidate against job posting using explainable 100-point AI weighted matrix",
)
async def evaluate_candidate(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoreBreakdownResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)
    score_repo = ScoreRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate or not candidate.resumes:
        raise NotFoundException(resource="Candidate / Resume", identifier=candidate_id)

    resume = candidate.resumes[0]

    # Timestamp-based caching check (CTO Directive #10 Cost Optimization)
    score_ent = await score_repo.get_by_job_and_candidate(job.id, candidate.id)
    if score_ent and score_ent.match_breakdown:
        score_updated = score_ent.updated_at
        job_updated = job.updated_at
        resume_updated = resume.updated_at

        if score_updated >= job_updated and score_updated >= resume_updated:
            from loguru import logger
            logger.info(f"Cache Hit for candidate {candidate.id} on job {job.id} - skipping LLM runs.")
            return ScoreBreakdownResponse(**score_ent.match_breakdown)

    breakdown = await ScoringEngineService.evaluate_candidate(job, resume)
    await score_repo.save_or_update_score(
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        breakdown=breakdown,
    )

    return breakdown


@router.post(
    "/batch-evaluate/{job_id}",
    response_model=List[RankedCandidateScore],
    status_code=status.HTTP_200_OK,
    summary="Batch score and rank all uploaded candidates for a Job Posting",
)
async def batch_evaluate_job_candidates(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RankedCandidateScore]:
    job_repo = JobRepository(db)
    resume_repo = ResumeRepository(db)
    score_repo = ScoreRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    resumes = await resume_repo.list_by_job(job_id)
    results = []

    for res in resumes:
        breakdown = await ScoringEngineService.evaluate_candidate(job, res)
        score_ent = await score_repo.save_or_update_score(
            job_id=job.id,
            candidate_id=res.candidate_id,
            resume_id=res.id,
            breakdown=breakdown,
        )

        results.append(
            RankedCandidateScore(
                score_id=str(score_ent.id),
                job_id=str(job.id),
                candidate_id=str(res.candidate_id),
                candidate_name=res.candidate.full_name,
                candidate_email=res.candidate.email,
                overall_score=breakdown.overall_score,
                mandatory_skills_score=breakdown.mandatory_skills.raw_score,
                experience_score=breakdown.experience.raw_score,
                breakdown=breakdown,
            )
        )

    results.sort(key=lambda x: x.overall_score, reverse=True)
    return results


@router.get(
    "/leaderboard/{job_id}",
    response_model=List[RankedCandidateScore],
    status_code=status.HTTP_200_OK,
    summary="Get ranked candidate leaderboard for a job posting",
)
async def get_job_leaderboard(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RankedCandidateScore]:
    score_repo = ScoreRepository(db)
    scores = await score_repo.get_leaderboard_for_job(job_id)

    rankings = []
    for s in scores:
        breakdown = ScoreBreakdownResponse(**s.match_breakdown) if s.match_breakdown else None
        if breakdown:
            rankings.append(
                RankedCandidateScore(
                    score_id=str(s.id),
                    job_id=str(s.job_id),
                    candidate_id=str(s.candidate_id),
                    candidate_name=s.candidate.full_name,
                    candidate_email=s.candidate.email,
                    overall_score=s.overall_score,
                    mandatory_skills_score=s.mandatory_skills_score,
                    experience_score=s.experience_score,
                    breakdown=breakdown,
                )
            )
    return rankings
