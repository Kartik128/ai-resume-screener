"""
Assessments API endpoints — GET, POST to manage micro-tests, submit responses,
and auto-calculate performance results.
"""
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.assessment import Assessment, AssessmentResponse
from app.models.candidate import Candidate
from app.models.job import Job

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class MCQChoice(BaseModel):
    choice_text: str
    is_correct: bool


class MCQQuestion(BaseModel):
    question_text: str
    choices: List[MCQChoice] = Field(..., min_length=2, max_length=5)


class AssessmentCreate(BaseModel):
    job_id: uuid.UUID
    title: str = Field(..., max_length=255)
    questions: List[MCQQuestion] = Field(..., min_length=1)
    time_limit_mins: int = Field(15, ge=1, le=120)


class AssessmentResponseSubmit(BaseModel):
    candidate_id: uuid.UUID
    answers: dict = Field(..., description="Map of {question_index: selected_choice_index}")


class QuestionOut(BaseModel):
    question_text: str
    choices: List[str]


class AssessmentPublicOut(BaseModel):
    assessment_id: uuid.UUID
    title: str
    time_limit_mins: int
    questions: List[QuestionOut]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a micro-test assessment for a Job Posting",
)
async def create_assessment(
    body: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify Job
    job_res = await db.execute(select(Job).where(Job.id == body.job_id, Job.company_id == current_user.company_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise NotFoundException(resource="Job", identifier=body.job_id)

    # Check if assessment exists
    res = await db.execute(select(Assessment).where(Assessment.job_id == body.job_id))
    asmt = res.scalar_one_or_none()

    q_dicts = [q.model_dump() for q in body.questions]

    if asmt:
        asmt.title = body.title
        asmt.questions_json = q_dicts
        asmt.time_limit_mins = body.time_limit_mins
    else:
        asmt = Assessment(
            job_id=body.job_id,
            title=body.title,
            questions_json=q_dicts,
            time_limit_mins=body.time_limit_mins,
        )
        db.add(asmt)

    await db.commit()
    return {"success": True, "assessment_id": str(asmt.id)}


@router.get(
    "/job/{job_id}",
    summary="Get assessment configurations linked to a job",
)
async def get_job_assessment(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Assessment).where(Assessment.job_id == job_id))
    asmt = res.scalar_one_or_none()
    if not asmt:
        return {"has_assessment": False, "assessment": None}

    return {
        "has_assessment": True,
        "assessment": {
            "id": str(asmt.id),
            "title": asmt.title,
            "time_limit_mins": asmt.time_limit_mins,
            "questions": asmt.questions_json
        }
    }


@router.get(
    "/{assessment_id}/public",
    response_model=AssessmentPublicOut,
    summary="Fetch public assessment questions for candidates (correct choices stripped to prevent cheating)",
)
async def get_public_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    asmt = res.scalar_one_or_none()
    if not asmt:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Strip correct answer flags
    stripped_questions = []
    for q in asmt.questions_json:
        stripped_questions.append(
            QuestionOut(
                question_text=q["question_text"],
                choices=[c["choice_text"] for c in q["choices"]]
            )
        )

    return AssessmentPublicOut(
        assessment_id=asmt.id,
        title=asmt.title,
        time_limit_mins=asmt.time_limit_mins,
        questions=stripped_questions
    )


@router.post(
    "/{assessment_id}/submit",
    status_code=status.HTTP_200_OK,
    summary="Submit micro-test answers and auto-grade score",
)
async def submit_answers(
    assessment_id: uuid.UUID,
    body: AssessmentResponseSubmit,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    asmt = res.scalar_one_or_none()
    if not asmt:
        raise HTTPException(status_code=404, detail="Assessment not found")

    questions = asmt.questions_json
    total_q = len(questions)
    correct_count = 0

    for idx, q in enumerate(questions):
        selected_idx = body.answers.get(str(idx)) or body.answers.get(idx)
        if selected_idx is not None:
            choices = q["choices"]
            if 0 <= int(selected_idx) < len(choices):
                if choices[int(selected_idx)]["is_correct"]:
                    correct_count += 1

    score_pct = round((correct_count / total_q) * 100, 1) if total_q > 0 else 0.0

    # Save Response
    resp = AssessmentResponse(
        assessment_id=assessment_id,
        candidate_id=body.candidate_id,
        answers_json=body.answers,
        score=score_pct
    )
    db.add(resp)
    await db.commit()

    return {"success": True, "score": score_pct, "correct_count": correct_count, "total_questions": total_q}


class CandidateSelfScheduleRequest(BaseModel):
    candidate_id: uuid.UUID
    scheduled_at: datetime


@router.post(
    "/{assessment_id}/schedule-candidate",
    status_code=status.HTTP_200_OK,
    summary="Public endpoint: Candidates self-schedule interview after submitting assessment tests",
)
async def public_self_schedule(
    assessment_id: uuid.UUID,
    body: CandidateSelfScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.models.application import Application, ApplicationStatus
    from app.models.pipeline_activity import PipelineActivity, ActivityType
    
    # 1. Load active assessment
    asmt_res = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    asmt = asmt_res.scalar_one_or_none()
    if not asmt:
        raise HTTPException(status_code=404, detail="Assessment config not found")

    # 2. Locate active application mapping
    app_res = await db.execute(
        select(Application).where(Application.candidate_id == body.candidate_id, Application.job_id == asmt.job_id)
    )
    app = app_res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="No active application found for this job-candidate pairing")

    # 3. Transition status and write to audit timeline
    old_status = app.status
    app.status = ApplicationStatus.INTERVIEWED

    act = PipelineActivity(
        application_id=app.id,
        activity_type=ActivityType.REMINDER_SET,
        from_value=old_status.value,
        to_value=ApplicationStatus.INTERVIEWED.value,
        note=f"📅 Candidate self-scheduled interview: {body.scheduled_at.strftime('%Y-%m-%d %H:%M')} (GMT)",
    )
    db.add(act)
    await db.commit()

    return {"success": True, "detail": "Interview scheduled successfully"}
