"""
Interview Intelligence API router. Exposes audio transcript uploads, details, and score alignment logs.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.transcript import InterviewTranscript

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class TranscriptOut(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    raw_transcript: str
    summary_analysis: Optional[str]
    alignment_score: float


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=TranscriptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Zoom/Teams audio file, simulate transcription, and run semantic scorecard matching",
)
async def upload_interview_audio(
    candidate_id: uuid.UUID = Form(...),
    job_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check extension
    filename = file.filename.lower()
    if not (filename.endswith('.mp3') or filename.endswith('.wav') or filename.endswith('.m4a') or filename.endswith('.mp4')):
        raise HTTPException(status_code=400, detail="Unsupported audio/video format. Provide MP3, WAV, or M4A.")

    from app.repositories.job_repository import JobRepository
    from app.repositories.candidate_repository import CandidateRepository

    job_repo = JobRepository(db)
    cand_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job Posting not found")

    candidate = await cand_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job_skills = [s.get("name", "").lower() for s in (job.parsed_data or {}).get("mandatory_skills", []) if s.get("name")]
    cand_skills = [s.lower() for s in (candidate.raw_skills or [])]

    matched_skills = [s for s in job_skills if s in cand_skills]
    missing_skills = [s for s in job_skills if s not in cand_skills]

    # Calculate dynamic alignment score
    base_score = 70.0
    if job_skills:
        match_ratio = len(matched_skills) / len(job_skills)
        base_score += (30.0 * match_ratio)
    alignment = round(min(base_score, 100.0), 1)

    # Dynamic transcript generation
    matched_skills_str = ", ".join(matched_skills) if matched_skills else "core software designs"
    simulated_transcript = (
        f"Interviewer: Welcome {candidate.full_name}! Let's discuss your skills for the {job.title} role.\n"
        f"Candidate: Thank you. I have extensive hands-on experience in software engineering, specifically working with {matched_skills_str}.\n"
        f"Interviewer: Great. How do you deal with high concurrency and database bottlenecks?\n"
        f"Candidate: In my previous projects, I resolved scaling limits by optimizing database queries, adding caching layers, and implementing load balancers.\n"
        f"Interviewer: Perfect. What are your views on code quality and unit testing?\n"
        f"Candidate: I make sure my code is fully covered by automated pipelines and regression checks before merging."
    )

    # Dynamic structured summary analysis
    strengths = f"Demonstrated expertise with: {matched_skills_str}." if matched_skills else "General software development background."
    flags = f"Vague detail on missing job criteria: {', '.join(missing_skills)}." if missing_skills else "No major technical gap flags detected."
    
    simulated_summary = (
        f"🎯 Key Technical Strengths: {strengths}\n\n"
        f"💬 Communication & Leadership: Articulate response structure, detailed answers on scaling, and proactive tone.\n\n"
        f"⚠️ Potential Flags: {flags}"
    )

    trans = InterviewTranscript(
        candidate_id=candidate_id,
        job_id=job_id,
        raw_transcript=simulated_transcript,
        summary_analysis=simulated_summary,
        alignment_score=alignment
    )
    db.add(trans)
    await db.commit()

    return TranscriptOut(
        id=trans.id,
        candidate_id=trans.candidate_id,
        job_id=trans.job_id,
        raw_transcript=trans.raw_transcript,
        summary_analysis=trans.summary_analysis,
        alignment_score=trans.alignment_score
    )


@router.get(
    "/candidate/{candidate_id}",
    response_model=Optional[TranscriptOut],
    summary="Fetch transcript intelligence profile for a specific candidate",
)
async def get_candidate_transcript(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(InterviewTranscript).where(InterviewTranscript.candidate_id == candidate_id)
    )
    trans = res.scalar_one_or_none()
    if not trans:
        return None

    return TranscriptOut(
        id=trans.id,
        candidate_id=trans.candidate_id,
        job_id=trans.job_id,
        raw_transcript=trans.raw_transcript,
        summary_analysis=trans.summary_analysis,
        alignment_score=trans.alignment_score
    )
