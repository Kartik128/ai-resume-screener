from typing import List, Optional, Any
from pydantic import BaseModel, Field


class HiringFunnelStage(BaseModel):
    stage: str
    count: int
    conversion_rate: float


class SkillFrequencyItem(BaseModel):
    skill_name: str
    count: int
    percentage: float


class HiringTrendItem(BaseModel):
    period: str
    applications: int
    shortlisted: int
    hires: int


class HRAnalyticsDashboardResponse(BaseModel):
    total_jobs: int
    total_candidates: int
    average_candidate_score: float
    average_time_to_hire_days: float
    hiring_funnel: List[HiringFunnelStage]
    top_candidate_skills: List[SkillFrequencyItem]
    top_skill_gaps: List[SkillFrequencyItem]
    hiring_trends: List[HiringTrendItem]
    recruiter_ai_agreement_rate: float
    candidate_experience_nps: float


class DataPoint(BaseModel):
    label: str
    value: Any


class NLAskRequest(BaseModel):
    question: str


class NLAnswerResponse(BaseModel):
    question: str
    category: str
    headline: str
    data_points: List[DataPoint]
    insight: str
    suggested_followups: List[str]

