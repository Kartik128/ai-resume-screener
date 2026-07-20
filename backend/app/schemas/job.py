import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.job import JobStatus
from app.schemas.skill import ExtractedSkill, SkillRead


class JobSkillRead(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    is_mandatory: bool
    min_experience_years: Optional[float] = None
    weight: float = 1.0
    skill: SkillRead

    model_config = ConfigDict(from_attributes=True)


class JobStructuredExtract(BaseModel):
    role: str = Field(..., description="Job title / role name")
    department: Optional[str] = None
    min_experience_years: Optional[float] = None
    max_experience_years: Optional[float] = None
    mandatory_skills: List[ExtractedSkill] = Field(default_factory=list)
    good_to_have_skills: List[ExtractedSkill] = Field(default_factory=list)
    education_requirement: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    responsibilities: List[str] = Field(default_factory=list)


class JobCreateText(BaseModel):
    title: Optional[str] = None
    raw_description: str = Field(..., min_length=20, description="Raw job description text")


class JobCreateSave(BaseModel):
    title: str = Field(..., max_length=255)
    department: Optional[str] = None
    raw_description: str
    status: JobStatus = JobStatus.ACTIVE
    min_experience_years: Optional[float] = None
    max_experience_years: Optional[float] = None
    education_requirement: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    responsibilities: List[str] = Field(default_factory=list)
    mandatory_skills: List[ExtractedSkill] = Field(default_factory=list)
    good_to_have_skills: List[ExtractedSkill] = Field(default_factory=list)


class JobRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    department: Optional[str] = None
    raw_description: str
    status: JobStatus
    min_experience_years: Optional[float] = None
    max_experience_years: Optional[float] = None
    education_requirement: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    responsibilities: Optional[List[str]] = Field(default_factory=list)
    parsed_data: Optional[Dict[str, Any]] = None
    job_skills: List[JobSkillRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
