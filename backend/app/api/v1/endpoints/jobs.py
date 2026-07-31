import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.job import (
    JobCreateSave,
    JobCreateText,
    JobRead,
    JobStructuredExtract,
)
from app.services.document_parser_service import DocumentParserService
from app.services.jd_parser_service import JDParserService

router = APIRouter()


@router.post(
    "/parse-text",
    response_model=JobStructuredExtract,
    status_code=status.HTTP_200_OK,
    summary="Parse raw Job Description text into structured AI JSON",
)
async def parse_jd_text(
    body: JobCreateText,
    current_user: User = Depends(get_current_user),
) -> JobStructuredExtract:
    return await JDParserService.parse_jd_text(body.raw_description)


@router.post(
    "/parse-file",
    response_model=JobStructuredExtract,
    status_code=status.HTTP_200_OK,
    summary="Extract text from uploaded JD file (PDF, DOCX, TXT) and convert to structured AI JSON",
)
async def parse_jd_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> JobStructuredExtract:
    raw_text = await DocumentParserService.parse_upload_file(file)
    return await JDParserService.parse_jd_text(raw_text)


@router.post(
    "/",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new Job Posting with mandatory & nice-to-have skills",
)
async def create_job(
    body: JobCreateSave,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    skill_repo = SkillRepository(db)
    job_repo = JobRepository(db)

    # Resolve / store skills in normalized Skill table
    mandatory_entities = []
    for skill_dto in body.mandatory_skills:
        s_entity = await skill_repo.get_or_create(
            name=skill_dto.name,
            category=skill_dto.category,
            synonyms=skill_dto.synonyms,
        )
        mandatory_entities.append(s_entity)

    good_entities = []
    for skill_dto in body.good_to_have_skills:
        s_entity = await skill_repo.get_or_create(
            name=skill_dto.name,
            category=skill_dto.category,
            synonyms=skill_dto.synonyms,
        )
        good_entities.append(s_entity)

    job = await job_repo.create_job_with_skills(
        company_id=current_user.company_id,
        creator_id=current_user.id,
        data=body,
        mandatory_skill_entities=mandatory_entities,
        good_skill_entities=good_entities,
    )

    return JobRead.model_validate(job)


@router.get(
    "/",
    response_model=List[JobRead],
    status_code=status.HTTP_200_OK,
    summary="List all job postings for the recruiter's company",
)
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[JobRead]:
    job_repo = JobRepository(db)
    jobs = await job_repo.list_by_company(current_user.company_id)
    return [JobRead.model_validate(j) for j in jobs]


@router.get(
    "/{job_id}",
    response_model=JobRead,
    status_code=status.HTTP_200_OK,
    summary="Get job details by ID",
)
async def get_job_by_id(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)
    return JobRead.model_validate(job)


from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy import select
from app.models.job import JobStatus
from app.schemas.skill import ExtractedSkill

class JobGenerateAIRequest(BaseModel):
    title: str
    department: Optional[str] = None
    key_skills: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    is_remote: bool = False

class JobCommentCreate(BaseModel):
    comment_text: str

class JobCommentRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    comment_text: str
    created_at: datetime


@router.post(
    "/generate-ai",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a Job Description using AI based on minimal inputs and save as DRAFT",
)
async def generate_jd_ai(
    body: JobGenerateAIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Simulated AI prompt content generation
    title = body.title
    dept = body.department or "Engineering"
    loc = body.location or "San Francisco, CA"
    remote_str = "Remote" if body.is_remote else "On-site"
    skills_str = ", ".join(body.key_skills) if body.key_skills else "software engineering, problem solving"
    
    # Draft a compelling description and lists
    description = (
        f"We are looking for a talented {title} to join our growing {dept} team in {loc} ({remote_str}). "
        f"In this role, you will leverage your expertise in {skills_str} to design, build, and maintain high-performance services. "
        f"You will work closely with product managers, designers, and other engineers to deliver customer-facing features."
    )
    
    responsibilities = [
        "Collaborate with cross-functional teams to design, develop, and deploy scalable solutions.",
        "Write clean, maintainable, and well-tested code following industry best practices.",
        "Analyze product specs and write detailed technical implementation plans.",
        "Perform code reviews and mentor junior developers in the team.",
        "Identify performance bottlenecks, troubleshoot issues, and optimize application speed."
    ]
    
    # Construct list of mandatory and good to have skills
    mandatory_skills = []
    good_to_have_skills = []
    
    # Add input skills as mandatory
    for s in body.key_skills:
        mandatory_skills.append(ExtractedSkill(name=s, category="technical"))
        
    # Standard engineering defaults if empty
    if not mandatory_skills:
        mandatory_skills.append(ExtractedSkill(name="Problem Solving", category="core"))
        mandatory_skills.append(ExtractedSkill(name="Software Design", category="technical"))
        
    good_to_have_skills.append(ExtractedSkill(name="CI/CD Pipelines", category="tools"))
    good_to_have_skills.append(ExtractedSkill(name="Cloud Platforms (AWS/GCP)", category="tools"))
    
    # Save a draft Job posting
    save_data = JobCreateSave(
        title=title,
        department=dept,
        raw_description=description,
        status=JobStatus.DRAFT,
        min_experience_years=3.0,
        max_experience_years=8.0,
        education_requirement="Bachelor's in Computer Science or equivalent",
        location=loc,
        is_remote=body.is_remote,
        min_salary=120000.0,
        max_salary=180000.0,
        salary_currency="USD",
        responsibilities=responsibilities,
        mandatory_skills=mandatory_skills,
        good_to_have_skills=good_to_have_skills
    )
    
    # Create the job with skills
    skill_repo = SkillRepository(db)
    job_repo = JobRepository(db)
    
    mandatory_entities = []
    for skill_dto in save_data.mandatory_skills:
        s_entity = await skill_repo.get_or_create(name=skill_dto.name, category=skill_dto.category)
        mandatory_entities.append(s_entity)
        
    good_entities = []
    for skill_dto in save_data.good_to_have_skills:
        s_entity = await skill_repo.get_or_create(name=skill_dto.name, category=skill_dto.category)
        good_entities.append(s_entity)
        
    job = await job_repo.create_job_with_skills(
        company_id=current_user.company_id,
        creator_id=current_user.id,
        data=save_data,
        mandatory_skill_entities=mandatory_entities,
        good_skill_entities=good_entities,
    )
    return JobRead.model_validate(job)


@router.put(
    "/{job_id}",
    response_model=JobRead,
    summary="Update an existing Job Description / Draft Details"
)
async def update_job(
    job_id: uuid.UUID,
    body: JobCreateSave,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)
        
    # Update properties
    job.title = body.title
    job.department = body.department
    job.raw_description = body.raw_description
    job.min_experience_years = body.min_experience_years
    job.max_experience_years = body.max_experience_years
    job.education_requirement = body.education_requirement
    job.location = body.location
    job.is_remote = body.is_remote
    job.min_salary = body.min_salary
    job.max_salary = body.max_salary
    job.salary_currency = body.salary_currency
    job.responsibilities = body.responsibilities
    
    # Flush changes
    db.add(job)
    await db.commit()
    
    # Reload and return
    updated_job = await job_repo.get_by_id(job_id, current_user.company_id)
    return JobRead.model_validate(updated_job)


@router.post(
    "/{job_id}/approve",
    response_model=JobRead,
    summary="Approve and Finalize a draft Job Description"
)
async def approve_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)
        
    job.status = JobStatus.ACTIVE
    db.add(job)
    await db.commit()
    
    updated_job = await job_repo.get_by_id(job_id, current_user.company_id)
    return JobRead.model_validate(updated_job)


@router.post(
    "/{job_id}/comments",
    response_model=JobCommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a collaborative review comment to a job posting draft"
)
async def add_job_comment(
    job_id: uuid.UUID,
    body: JobCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.comment import JobComment
    comment = JobComment(
        job_id=job_id,
        user_id=current_user.id,
        comment_text=body.comment_text
    )
    db.add(comment)
    await db.commit()
    
    # Query with joined relationship
    res = await db.execute(
        select(JobComment)
        .where(JobComment.id == comment.id)
    )
    loaded_comment = res.scalar_one()
    
    return JobCommentRead(
        id=loaded_comment.id,
        job_id=loaded_comment.job_id,
        user_id=loaded_comment.user_id,
        user_name=loaded_comment.user.full_name,
        comment_text=loaded_comment.comment_text,
        created_at=loaded_comment.created_at
    )


@router.get(
    "/{job_id}/comments",
    response_model=List[JobCommentRead],
    summary="List all collaborative comments on a job posting draft"
)
async def list_job_comments(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.comment import JobComment
    res = await db.execute(
        select(JobComment)
        .where(JobComment.job_id == job_id)
        .order_by(JobComment.created_at.asc())
    )
    comments = res.scalars().all()
    
    return [
        JobCommentRead(
            id=c.id,
            job_id=c.job_id,
            user_id=c.user_id,
            user_name=c.user.full_name,
            comment_text=c.comment_text,
            created_at=c.created_at
        )
        for c in comments
    ]
