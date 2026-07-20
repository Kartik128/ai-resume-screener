import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.schemas.summary import CandidateSummaryResponse
from app.services.summary_service import SummaryService

router = APIRouter()


@router.get(
    "/{job_id}/{candidate_id}",
    response_model=CandidateSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate recruiter-friendly AI summary, missing skills highlight, and gap warnings for candidate",
)
async def get_candidate_summary_and_gaps(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateSummaryResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate or not candidate.resumes:
        raise NotFoundException(resource="Candidate / Resume", identifier=candidate_id)

    resume = candidate.resumes[0]
    return await SummaryService.generate_summary(job, resume)
