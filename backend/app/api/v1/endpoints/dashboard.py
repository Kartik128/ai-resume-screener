import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.application import ApplicationStatus
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.score_repository import ScoreRepository
from app.schemas.dashboard import (
    ApplicationUpdateStatusRequest,
    CandidateCardResponse,
    CandidateComparisonColumn,
    CompareCandidatesRequest,
    ComparisonResponse,
    RecruiterFeedbackCreate,
)
from app.schemas.scoring import ScoreBreakdownResponse
from app.services.comparison_service import ComparisonService
from app.services.scoring_engine_service import ScoringEngineService
from app.services.summary_service import SummaryService

router = APIRouter()


@router.get(
    "/job/{job_id}/candidates",
    response_model=List[CandidateCardResponse],
    status_code=status.HTTP_200_OK,
    summary="Get candidate cards for Recruiter Dashboard (Shortlist, Reject, Maybe filters)",
)
async def get_dashboard_candidate_cards(
    job_id: uuid.UUID,
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CandidateCardResponse]:
    job_repo = JobRepository(db)
    app_repo = ApplicationRepository(db)
    resume_repo = ResumeRepository(db)
    score_repo = ScoreRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    resumes = await resume_repo.list_by_job(job_id)
    cards: List[CandidateCardResponse] = []

    for res in resumes:
        app_ent = await app_repo.get_or_create(
            job_id=job_id, candidate_id=res.candidate_id, recruiter_id=current_user.id
        )

        if status_filter and app_ent.status != status_filter:
            continue

        score_ent = await score_repo.get_by_job_and_candidate(job_id, res.candidate_id)
        if not score_ent:
            breakdown = await ScoringEngineService.evaluate_candidate(job, res)
            score_ent = await score_repo.save_or_update_score(
                job_id=job.id,
                candidate_id=res.candidate_id,
                resume_id=res.id,
                breakdown=breakdown,
            )
        else:
            breakdown = (
                ScoreBreakdownResponse(**score_ent.match_breakdown)
                if score_ent.match_breakdown
                else None
            )

        summary_res = await SummaryService.generate_summary(job, res)

        cards.append(
            CandidateCardResponse(
                application_id=app_ent.id,
                job_id=job_id,
                candidate_id=res.candidate_id,
                resume_id=res.id,
                full_name=res.candidate.full_name,
                email=res.candidate.email,
                phone=res.candidate.phone,
                location=res.candidate.location,
                total_experience_years=res.candidate.total_experience_years,
                status=app_ent.status,
                notes=app_ent.notes,
                overall_score=score_ent.overall_score,
                score_breakdown=breakdown,
                summary_text=summary_res.executive_summary,
            )
        )

    cards.sort(key=lambda c: c.overall_score, reverse=True)
    return cards


@router.patch(
    "/application/{application_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update candidate status (Shortlist, Reject, Maybe, Interviewed, Offer Released, Joined)",
)
async def update_candidate_status(
    application_id: uuid.UUID,
    body: ApplicationUpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app_repo = ApplicationRepository(db)
    app_ent = await app_repo.get_by_id(application_id)
    if not app_ent:
        raise NotFoundException(resource="Candidate Application", identifier=application_id)

    updated = await app_repo.update_status(application_id, body.status, body.notes)
    return {"success": True, "application_id": str(updated.id), "status": updated.status.value}


@router.post(
    "/compare",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Side-by-side matrix comparison of 2 to 5 candidates",
)
async def compare_candidates_side_by_side(
    body: CompareCandidatesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonResponse:
    return await ComparisonService.compare_candidates(
        job_id=body.job_id,
        candidate_ids=body.candidate_ids,
        company_id=current_user.company_id,
        db=db,
    )


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    summary="Submit recruiter action feedback (Shortlisted, Rejected, Selected, Joined) to improve future recommendations",
)
async def submit_recruiter_feedback(
    body: RecruiterFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fb_repo = FeedbackRepository(db)
    fb = await fb_repo.create_feedback(
        job_id=body.job_id,
        candidate_id=body.candidate_id,
        recruiter_id=current_user.id,
        action=body.action,
        rating=body.rating,
        feedback_text=body.feedback_text,
    )
    return {"success": True, "feedback_id": str(fb.id), "action": fb.action.value}
