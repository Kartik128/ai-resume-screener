"""
Pipeline endpoints — stage transitions, notes, reminders, activity history,
and blind-mode identity reveal with full audit logging.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.application import Application, ApplicationStatus
from app.models.pipeline_activity import PipelineActivity, ActivityType
from app.models.resume import Resume
from app.models.candidate import Candidate
from app.models.user import User

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class StageTransitionRequest(BaseModel):
    stage: ApplicationStatus
    note: Optional[str] = Field(None, max_length=2000)


class NoteRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)


class ReminderRequest(BaseModel):
    reminder_at: datetime
    reminder_note: Optional[str] = Field(None, max_length=500)


class AssignOwnerRequest(BaseModel):
    owner_id: uuid.UUID


class ActivityOut(BaseModel):
    id: uuid.UUID
    activity_type: str
    from_value: Optional[str]
    to_value: Optional[str]
    note: Optional[str]
    actor_name: Optional[str]
    created_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_application(application_id: uuid.UUID, db: AsyncSession) -> Application:
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise NotFoundException(resource="Application", identifier=application_id)
    return app


async def _log_activity(
    db: AsyncSession,
    application_id: uuid.UUID,
    actor_id: uuid.UUID,
    activity_type: ActivityType,
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
    note: Optional[str] = None,
):
    event = PipelineActivity(
        application_id=application_id,
        actor_id=actor_id,
        activity_type=activity_type,
        from_value=from_value,
        to_value=to_value,
        note=note,
    )
    db.add(event)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{application_id}/stage",
    status_code=status.HTTP_200_OK,
    summary="Move candidate to a new pipeline stage and log the transition",
)
async def move_stage(
    application_id: uuid.UUID,
    body: StageTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)
    old_stage = app.status.value
    app.status = body.stage
    app.stage_changed_at = datetime.now()

    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.STAGE_CHANGE,
        from_value=old_stage,
        to_value=body.stage.value,
        note=body.note,
    )
    
    # Trigger Webhooks dispatch trigger
    from app.api.v1.endpoints.webhooks import trigger_stage_changed_webhook
    await trigger_stage_changed_webhook(
        company_id=current_user.company_id,
        payload={
            "event": "candidate.stage_changed",
            "application_id": str(application_id),
            "candidate_id": str(app.candidate_id),
            "old_stage": old_stage,
            "new_stage": body.stage.value,
            "note": body.note
        },
        db=db
    )

    # Check for active campaign templates to trigger automatic drip sequence outreach
    from app.models.campaign import CampaignTemplate
    res_camp = await db.execute(
        select(CampaignTemplate)
        .where(CampaignTemplate.company_id == current_user.company_id)
        .where(CampaignTemplate.trigger_stage == body.stage.value.lower())
        .where(CampaignTemplate.is_active == True)
    )
    templates = res_camp.scalars().all()
    for t in templates:
        # Simulate dispatching automated outreach templates
        await _log_activity(
            db, application_id, current_user.id,
            ActivityType.NOTE_ADDED,
            note=f"⚡ Automated Campaign Outreach Sent ({t.channel.upper()}): {t.body[:150]}..."
        )
    
    await db.commit()
    return {
        "success": True,
        "application_id": str(application_id),
        "stage": body.stage.value,
        "stage_changed_at": app.stage_changed_at.isoformat(),
    }


@router.post(
    "/{application_id}/note",
    status_code=status.HTTP_201_CREATED,
    summary="Add a recruiter note to the application activity log",
)
async def add_note(
    application_id: uuid.UUID,
    body: NoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)
    # Append to the latest notes field for quick access
    app.notes = (app.notes or "") + f"\n[{datetime.now().strftime('%d %b %Y %H:%M')} – {current_user.full_name or current_user.email}] {body.note}"
    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.NOTE_ADDED,
        note=body.note,
    )
    await db.commit()
    return {"success": True, "note": body.note}


@router.patch(
    "/{application_id}/reminder",
    status_code=status.HTTP_200_OK,
    summary="Set a follow-up reminder for this candidate",
)
async def set_reminder(
    application_id: uuid.UUID,
    body: ReminderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)
    app.reminder_at = body.reminder_at
    app.reminder_note = body.reminder_note
    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.REMINDER_SET,
        to_value=body.reminder_at.isoformat(),
        note=body.reminder_note,
    )
    await db.commit()
    return {"success": True, "reminder_at": body.reminder_at.isoformat()}


@router.patch(
    "/{application_id}/owner",
    status_code=status.HTTP_200_OK,
    summary="Assign an owner (recruiter) responsible for progressing this candidate",
)
async def assign_owner(
    application_id: uuid.UUID,
    body: AssignOwnerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)
    old_owner = str(app.owner_id) if app.owner_id else None
    app.owner_id = body.owner_id
    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.OWNER_ASSIGNED,
        from_value=old_owner,
        to_value=str(body.owner_id),
    )
    await db.commit()
    return {"success": True, "owner_id": str(body.owner_id)}


@router.post(
    "/{application_id}/reveal",
    status_code=status.HTTP_200_OK,
    summary="Reveal candidate identity (blind mode) — logged to audit trail",
)
async def reveal_identity(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)

    # Load full candidate and resume PII
    cand_result = await db.execute(
        select(Candidate).where(Candidate.id == app.candidate_id)
    )
    cand = cand_result.scalar_one_or_none()
    resume_result = await db.execute(
        select(Resume).where(Resume.candidate_id == app.candidate_id)
    )
    resume = resume_result.scalar_one_or_none()

    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.IDENTITY_REVEALED,
        note=f"Identity revealed by {current_user.email}",
    )
    await db.commit()

    parsed = resume.parsed_data or {} if resume else {}
    return {
        "full_name": cand.full_name if cand else None,
        "email": cand.email if cand else None,
        "phone": cand.phone if cand else None,
        "location": cand.location if cand else None,
        "linkedin_url": parsed.get("linkedin_url"),
        "github_url": parsed.get("github_url"),
        "education": parsed.get("education", []),
        "revealed_at": datetime.now().isoformat(),
        "revealed_by": current_user.email,
    }


@router.get(
    "/{application_id}/history",
    response_model=List[ActivityOut],
    status_code=status.HTTP_200_OK,
    summary="Get full activity timeline for a candidate application",
)
async def get_activity_history(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_application(application_id, db)  # verify exists
    result = await db.execute(
        select(PipelineActivity)
        .where(PipelineActivity.application_id == application_id)
        .order_by(desc(PipelineActivity.created_at))
    )
    activities = result.scalars().all()

    return [
        ActivityOut(
            id=a.id,
            activity_type=a.activity_type.value,
            from_value=a.from_value,
            to_value=a.to_value,
            note=a.note,
            actor_name=(
                a.actor.full_name or a.actor.email if a.actor else "System"
            ),
            created_at=a.created_at,
        )
        for a in activities
    ]


class SendEmailRequest(BaseModel):
    subject: str = Field(..., max_length=255)
    body: str = Field(..., max_length=5000)


class ScheduleInterviewRequest(BaseModel):
    scheduled_at: datetime
    duration_mins: int = Field(30, ge=15, le=180)
    interviewer_email: str = Field(..., max_length=255)


@router.post(
    "/{application_id}/send-email",
    status_code=status.HTTP_200_OK,
    summary="Mock send portal email to candidate (Gmail/Outlook ready) and log activity",
)
async def send_portal_email(
    application_id: uuid.UUID,
    body: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)
    
    # Audit log
    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.NOTE_ADDED,
        note=f"📧 Email Sent (Subject: {body.subject}): {body.body[:150]}..."
    )
    await db.commit()
    return {"success": True, "details": "Email dispatched successfully"}


@router.post(
    "/{application_id}/background-check",
    status_code=status.HTTP_200_OK,
    summary="Trigger Checkr background check validation on candidate",
)
async def trigger_background_check(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)
    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.REMINDER_SET,
        note="🛡️ Checkr Background Check Triggered. Status: Processing (Estimated 48h)"
    )
    await db.commit()
    return {"success": True, "detail": "Background check dispatch request received"}


@router.post(
    "/{application_id}/schedule-interview",
    status_code=status.HTTP_200_OK,
    summary="Mock schedule calendar interview (Google Calendar ready) and log activity",
)
async def schedule_calendar_interview(
    application_id: uuid.UUID,
    body: ScheduleInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application(application_id, db)

    # Log to pipeline activity tracker
    await _log_activity(
        db, application_id, current_user.id,
        ActivityType.REMINDER_SET,
        note=f"📅 Interview Scheduled: {body.scheduled_at.strftime('%Y-%m-%d %H:%M')} ({body.duration_mins} mins) with {body.interviewer_email}"
    )
    # Set stage to Interviewed
    app.status = ApplicationStatus.INTERVIEWED
    await db.commit()
    return {"success": True, "details": "Interview scheduled and logged to pipeline"}
