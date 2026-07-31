import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.application import ApplicationStatus
from app.models.scorecard import Scorecard
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

# ── Helper: load custom scorecard weights for a job ───────────────────────────

async def _load_scorecard_weights(job_id: uuid.UUID, db: AsyncSession) -> Optional[dict]:
    result = await db.execute(select(Scorecard).where(Scorecard.job_id == job_id))
    sc = result.scalar_one_or_none()
    if not sc:
        return None
    return {
        "mandatory_skills": sc.w_mandatory_skills,
        "experience": sc.w_experience,
        "nice_to_have": sc.w_nice_to_have,
        "career_stability": sc.w_career_stability,
        "industry_match": sc.w_industry_match,
        "education": sc.w_education,
        "certifications": sc.w_certifications,
        "location": sc.w_location,
    }

# ── Helper: anonymize a CandidateCardResponse for blind mode ─────────────────

def _anonymize(card: CandidateCardResponse, index: int) -> CandidateCardResponse:
    """Replace all identity signals with a neutral alias."""
    alias = f"Candidate #{chr(65 + index)}"  # Candidate #A, #B, #C …
    return card.model_copy(update={
        "full_name": alias,
        "email": None,
        "phone": None,
        "location": "Hidden",
    })


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

    # Load custom scorecard weights (if recruiter has customised them)
    custom_weights = await _load_scorecard_weights(job_id, db)

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
            breakdown = await ScoringEngineService.evaluate_candidate(
                job, res, custom_weights=custom_weights
            )
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

        # Query duplicate status
        from app.models.duplicate_candidate import DuplicateCandidate
        dup_res = await db.execute(
            select(DuplicateCandidate).where(DuplicateCandidate.duplicate_id == res.candidate_id)
        )
        dup_ent = dup_res.scalar_one_or_none()

        # Query assessment response score
        from app.models.assessment import Assessment, AssessmentResponse
        asmt_score = None
        asmt_res = await db.execute(
            select(AssessmentResponse)
            .join(Assessment, Assessment.id == AssessmentResponse.assessment_id)
            .where(Assessment.job_id == job_id, AssessmentResponse.candidate_id == res.candidate_id)
        )
        asmt_resp_ent = asmt_res.scalars().first()
        if asmt_resp_ent:
            asmt_score = asmt_resp_ent.score

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
                score_id=score_ent.id,
                duplicate_detected=True if dup_ent else False,
                original_candidate_id=dup_ent.canonical_id if dup_ent else None,
                assessment_score=asmt_score,
                is_internal=res.candidate.is_internal,
            )
        )

    cards.sort(key=lambda c: c.overall_score, reverse=True)

    # ── Calibration Pass: calculate relative ranks, ties, outliers & low-evidence warnings ──
    n_cards = len(cards)
    if n_cards > 0:
        # Calculate mean & standard deviation for outlier check
        scores = [c.overall_score for c in cards]
        mean = sum(scores) / n_cards
        variance = sum((x - mean) ** 2 for x in scores) / n_cards
        std_dev = (variance ** 0.5) if variance > 0 else 0.0

        for idx, card in enumerate(cards):
            flags = []
            # 1. Percentile Rank
            card.rank_percentile = round(((n_cards - 1 - idx) / max(1, n_cards - 1)) * 100, 1)

            # 2. Tie warnings (within 2 points of neighbors)
            has_tie = False
            if idx > 0 and abs(card.overall_score - cards[idx - 1].overall_score) <= 2.0:
                has_tie = True
            if idx < n_cards - 1 and abs(card.overall_score - cards[idx + 1].overall_score) <= 2.0:
                has_tie = True
            if has_tie:
                flags.append("TIE")

            # 3. Outlier check (more than 2 standard deviations away from mean)
            if std_dev > 0.0 and abs(card.overall_score - mean) > (2 * std_dev):
                flags.append("OUTLIER")

            # 4. Low Evidence check (short experience text or missing breakdown)
            # Find the resume to check word count
            r_idx = next((i for i, r in enumerate(resumes) if r.candidate_id == card.candidate_id), None)
            if r_idx is not None:
                exp_text = resumes[r_idx].candidate.summary or ""
                if len(exp_text.split()) < 40:
                    flags.append("LOW_EVIDENCE")

            card.calibration_flags = flags

    # Apply blind mode — anonymize PII if enabled on this job
    if job.blind_mode:
        cards = [_anonymize(card, i) for i, card in enumerate(cards)]

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
