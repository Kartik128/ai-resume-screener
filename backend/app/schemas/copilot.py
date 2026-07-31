from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class QuestionCategory(str, Enum):
    TECHNICAL = "TECHNICAL"
    BEHAVIORAL = "BEHAVIORAL"
    RESUME_DEEP_DIVE = "RESUME_DEEP_DIVE"
    CLAIM_VERIFICATION = "CLAIM_VERIFICATION"


class InterviewQuestionItem(BaseModel):
    category: QuestionCategory
    question: str
    rationale: str
    expected_answer_signal: str


class PersonalizedInterviewQuestionsResponse(BaseModel):
    candidate_id: str
    job_id: str
    questions: List[InterviewQuestionItem]


class RedFlagType(str, Enum):
    EMPLOYMENT_GAP = "EMPLOYMENT_GAP"
    JOB_HOPPING = "JOB_HOPPING"
    TIMELINE_INCONSISTENCY = "TIMELINE_INCONSISTENCY"
    MISSING_EDUCATION = "MISSING_EDUCATION"
    POSSIBLE_FAKE_EXP = "POSSIBLE_FAKE_EXP"
    OVERQUALIFIED = "OVERQUALIFIED"
    UNDERQUALIFIED = "UNDERQUALIFIED"
    DUPLICATE_RESUME = "DUPLICATE_RESUME"


class FlagSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RedFlagItem(BaseModel):
    flag_type: RedFlagType
    severity: FlagSeverity
    description: str
    evidence: str


class RedFlagAnalysisResponse(BaseModel):
    candidate_id: str
    job_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    has_critical_flags: bool
    red_flags: List[RedFlagItem]


class CopilotChatRequest(BaseModel):
    job_id: str
    candidate_id: Optional[str] = None
    question: str


class CopilotChatResponse(BaseModel):
    answer: str
    suggested_followups: List[str]
