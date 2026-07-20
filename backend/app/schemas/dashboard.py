import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.application import ApplicationStatus
from app.models.feedback import RecruiterAction
from app.schemas.scoring import ScoreBreakdownResponse


class CandidateCardResponse(BaseModel):
    application_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    resume_id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    total_experience_years: Optional[float] = None
    status: ApplicationStatus
    notes: Optional[str] = None
    overall_score: float
    score_breakdown: Optional[ScoreBreakdownResponse] = None
    summary_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationUpdateStatusRequest(BaseModel):
    status: ApplicationStatus
    notes: Optional[str] = None


class CompareCandidatesRequest(BaseModel):
    job_id: uuid.UUID
    candidate_ids: List[uuid.UUID] = Field(..., min_length=2, max_length=5)


class CandidateComparisonColumn(BaseModel):
    candidate_id: uuid.UUID
    full_name: str
    overall_score: float
    mandatory_skills_score: float
    experience_score: float
    total_experience_years: float
    location: Optional[str] = None
    mandatory_skills_present: List[str]
    missing_skills: List[str]
    risk_score: float


class ComparisonResponse(BaseModel):
    job_id: uuid.UUID
    job_title: str
    recommended_top_candidate_id: uuid.UUID
    recommendation_reasoning: str
    columns: List[CandidateComparisonColumn]


class RecruiterFeedbackCreate(BaseModel):
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    action: RecruiterAction
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    feedback_text: Optional[str] = None
