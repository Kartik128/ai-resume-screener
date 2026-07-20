from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MatchType(str, Enum):
    EXACT = "EXACT"
    SEMANTIC = "SEMANTIC"
    CONCEPTUAL = "CONCEPTUAL"
    MISSING = "MISSING"


class SkillMatchDetail(BaseModel):
    required_skill: str = Field(..., description="Skill required by Job")
    matched_candidate_skill: Optional[str] = Field(None, description="Skill found in Candidate profile")
    match_type: MatchType = Field(..., description="Degree of match")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score between 0.0 and 1.0")
    reasoning: str = Field(..., description="Explanation of why this matches or is missing")


class SemanticMatchRequest(BaseModel):
    required_skills: List[str] = Field(..., description="List of skills required by job posting")
    candidate_skills: List[str] = Field(..., description="List of skills extracted from candidate resume")
    candidate_experience_text: Optional[str] = Field(None, description="Optional raw candidate experience text")


class SemanticMatchResponse(BaseModel):
    semantic_matches: List[SkillMatchDetail]
    overall_semantic_score: float = Field(..., ge=0.0, le=100.0)
