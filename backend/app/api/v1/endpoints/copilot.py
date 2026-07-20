import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.schemas.copilot import (
    PersonalizedInterviewQuestionsResponse,
    RedFlagAnalysisResponse,
)
from app.services.interview_service import InterviewService
from app.services.red_flag_service import RedFlagService

router = APIRouter()


@router.get(
    "/interview-questions/{job_id}/{candidate_id}",
    response_model=PersonalizedInterviewQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate 5-7 personalized, non-generic interview questions referencing candidate resume claims",
)
async def get_personalized_interview_questions(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonalizedInterviewQuestionsResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate or not candidate.resumes:
        raise NotFoundException(resource="Candidate / Resume", identifier=candidate_id)

    resume = candidate.resumes[0]
    return await InterviewService.generate_questions(job, resume)


@router.get(
    "/red-flags/{job_id}/{candidate_id}",
    response_model=RedFlagAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run forensic anomaly detection for employment gaps, job hopping, timeline inconsistencies, and fake experience indicators",
)
async def analyze_candidate_red_flags(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedFlagAnalysisResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate or not candidate.resumes:
        raise NotFoundException(resource="Candidate / Resume", identifier=candidate_id)

    resume = candidate.resumes[0]
    return await RedFlagService.analyze_red_flags(job, resume)
