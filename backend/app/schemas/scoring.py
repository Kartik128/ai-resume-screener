from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ComponentScore(BaseModel):
    weight_percentage: float = Field(..., description="Weight allocation e.g. 35.0 for 35%")
    raw_score: float = Field(..., ge=0.0, le=100.0, description="Raw score 0 to 100")
    weighted_score: float = Field(..., description="Weighted contribution to overall score")
    reasoning: str = Field(..., description="Explainable AI reasoning for this score")


class ScoreBreakdownResponse(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    mandatory_skills: ComponentScore
    experience: ComponentScore
    industry_match: ComponentScore
    nice_to_have_skills: ComponentScore
    career_stability: ComponentScore
    education: ComponentScore
    location: ComponentScore
    certifications: ComponentScore
    match_summary: str

    model_config = ConfigDict(from_attributes=True)


class RankedCandidateScore(BaseModel):
    score_id: str
    job_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    overall_score: float
    mandatory_skills_score: float
    experience_score: float
    breakdown: ScoreBreakdownResponse
