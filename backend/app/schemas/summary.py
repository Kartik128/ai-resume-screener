from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class FitRecommendation(str, Enum):
    STRONG_FIT = "STRONG_FIT"
    MODERATE_FIT = "MODERATE_FIT"
    WEAK_FIT = "WEAK_FIT"


class CandidateSummaryResponse(BaseModel):
    executive_summary: str = Field(..., description="Recruiter-friendly 2-3 sentence executive summary")
    key_strengths: List[str] = Field(default_factory=list)
    missing_mandatory_skills: List[str] = Field(default_factory=list)
    weak_experience_warning: Optional[str] = None
    salary_mismatch_warning: Optional[str] = None
    location_mismatch_warning: Optional[str] = None
    fit_recommendation: FitRecommendation = FitRecommendation.MODERATE_FIT
