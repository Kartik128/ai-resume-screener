import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.resume import ParsingStatus


class WorkExperienceDTO(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    skills_used: List[str] = Field(default_factory=list)


class EducationDTO(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    gpa: Optional[str] = None


class SkillItemDTO(BaseModel):
    name: str
    category: Optional[str] = None


class ProjectDTO(BaseModel):
    name: str
    description: Optional[str] = None
    technologies_used: List[str] = Field(default_factory=list)


class CertificationDTO(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    year: Optional[str] = None


class ResumeStructuredExtract(BaseModel):
    name: str = Field(..., description="Full candidate name")
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None
    total_experience_years: Optional[float] = 0.0
    work_experience: List[WorkExperienceDTO] = Field(default_factory=list)
    education: List[EducationDTO] = Field(default_factory=list)
    skills: List[SkillItemDTO] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    projects: List[ProjectDTO] = Field(default_factory=list)
    certifications: List[CertificationDTO] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)


class ResumeRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    raw_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    parsing_status: ParsingStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BulkUploadResponse(BaseModel):
    total_uploaded: int
    successful_count: int
    failed_count: int
    resumes: List[ResumeRead]
