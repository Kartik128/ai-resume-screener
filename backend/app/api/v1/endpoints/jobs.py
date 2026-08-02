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
from app.core.config import settings
import openai

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


import json

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
    title = body.title
    dept = body.department or "Engineering"
    loc = body.location or "San Francisco, CA"
    remote_str = "Remote" if body.is_remote else "On-site"
    skills_str = ", ".join(body.key_skills) if body.key_skills else "not specified"

    # Default values for fallback
    description = ""
    responsibilities = []
    mandatory_skills = []
    good_to_have_skills = []
    min_exp = 3.0
    max_exp = 8.0
    edu_req = "Bachelor's degree or equivalent experience"
    min_sal = 80000.0
    max_sal = 150000.0
    sal_curr = "USD"

    # Check if OpenAI API Key is configured
    if settings.OPENAI_API_KEY:
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""
            Generate a professional Job Description for the following role:
            Title: {title}
            Department: {dept}
            Location: {loc} ({remote_str})
            Requested Skills: {skills_str}

            Provide your response in JSON format matching this schema:
            {{
                "description": "2-3 sentence overview of the role...",
                "responsibilities": ["Responsibility 1", "Responsibility 2", "Responsibility 3", "Responsibility 4", "Responsibility 5"],
                "mandatory_skills": [
                    {{"name": "Skill Name 1", "category": "technical/core/tools"}},
                    {{"name": "Skill Name 2", "category": "technical/core/tools"}}
                ],
                "good_to_have_skills": [
                    {{"name": "Skill A", "category": "technical/core/tools"}},
                    {{"name": "Skill B", "category": "technical/core/tools"}}
                ],
                "min_experience_years": 3.0,
                "max_experience_years": 8.0,
                "education_requirement": "Bachelor's degree in related field or equivalent experience",
                "min_salary": 90000.0,
                "max_salary": 140000.0,
                "salary_currency": "USD"
            }}
            """
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert HR recruiter and talent advisor. Generate factual and correct job descriptions matching the requested department and title. Never output developer/programming requirements for non-technical roles."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            data = json.loads(response.choices[0].message.content)
            description = data.get("description", "")
            responsibilities = data.get("responsibilities", [])
            min_exp = float(data.get("min_experience_years", 3.0))
            max_exp = float(data.get("max_experience_years", 8.0))
            edu_req = data.get("education_requirement", edu_req)
            min_sal = float(data.get("min_salary", 120000.0))
            max_sal = float(data.get("max_salary", 180000.0))
            sal_curr = data.get("salary_currency", "USD")

            for s in data.get("mandatory_skills", []):
                mandatory_skills.append(ExtractedSkill(name=s["name"], category=s.get("category", "technical")))
            for s in data.get("good_to_have_skills", []):
                good_to_have_skills.append(ExtractedSkill(name=s["name"], category=s.get("category", "technical")))

        except Exception as e:
            # Clear lists for fallback if error occurs
            mandatory_skills = []
            good_to_have_skills = []

    # If OpenAI failed or is not configured, run robust domain-aware fallback generator
    if not responsibilities:
        dept_l = dept.lower()
        if "human" in dept_l or "hr" in dept_l or "talent" in dept_l:
            description = (
                f"We are looking for a talented {title} to join our growing {dept} team in {loc} ({remote_str}). "
                f"In this role, you will leverage your expertise in {skills_str} to attract, recruit, and onboard top-tier talent. "
                f"You will work closely with department heads and HR partners to scale our teams."
            )
            responsibilities = [
                "Manage full-cycle recruitment processes, including sourcing, screening, and interviewing candidates.",
                "Partner with hiring managers to understand department resource plans and role requirements.",
                "Coordinate interview schedules, feedback collection, and offer letter preparation.",
                "Optimize talent pipeline metrics and enhance the candidate experience.",
                "Participate in employer branding initiatives and talent networking events."
            ]
            min_exp, max_exp = 3.0, 8.0
            edu_req = "Bachelor's degree in Human Resources, Business, or equivalent experience"
            min_sal, max_sal = 80000.0, 130000.0
            mandatory_skills = [ExtractedSkill(name=s, category="core") for s in body.key_skills] or [
                ExtractedSkill(name="Sourcing", category="core"),
                ExtractedSkill(name="Candidate Experience", category="core")
            ]
            good_to_have_skills = [
                ExtractedSkill(name="Applicant Tracking Systems (ATS)", category="tools"),
                ExtractedSkill(name="Employer Branding", category="core")
            ]
        elif "sales" in dept_l or "market" in dept_l:
            description = (
                f"We are looking for a talented {title} to join our growing {dept} team in {loc} ({remote_str}). "
                f"In this role, you will leverage your expertise in {skills_str} to drive brand growth, customer acquisition, and market revenue. "
                f"You will work closely with product and client relations teams."
            )
            responsibilities = [
                "Develop and execute targeted sales/marketing campaigns to generate qualified pipelines.",
                "Manage client relationships, product demonstrations, and account negotiation workflows.",
                "Analyze market trends and competitor movements to optimize growth strategy.",
                "Present regular reports on sales targets, campaign ROI, and customer engagement metrics."
            ]
            min_exp, max_exp = 3.0, 8.0
            edu_req = "Bachelor's degree in Marketing, Business, or equivalent experience"
            min_sal, max_sal = 75000.0, 140000.0
            mandatory_skills = [ExtractedSkill(name=s, category="core") for s in body.key_skills] or [
                ExtractedSkill(name="Lead Generation", category="core"),
                ExtractedSkill(name="Negotiation", category="core")
            ]
            good_to_have_skills = [
                ExtractedSkill(name="CRM Tools (Salesforce/HubSpot)", category="tools"),
                ExtractedSkill(name="Market Analytics", category="core")
            ]
        elif "finance" in dept_l or "accounting" in dept_l:
            description = (
                f"We are looking for a talented {title} to join our growing {dept} team in {loc} ({remote_str}). "
                f"In this role, you will leverage your expertise in {skills_str} to audit financial profiles, manage budgets, and perform forecasting. "
                f"You will work closely with department executives and corporate leaders."
            )
            responsibilities = [
                "Manage corporate budgets, financial audits, and quarterly forecasting processes.",
                "Prepare accurate financial statements, cost projections, and expense compliance reviews.",
                "Identify cost optimization pathways and report on operational budget utilisation.",
                "Ensure adherence to regulatory financial auditing standards and internal tax policies."
            ]
            min_exp, max_exp = 4.0, 10.0
            edu_req = "Bachelor's degree in Finance, Accounting, Economics, or equivalent"
            min_sal, max_sal = 90000.0, 160000.0
            mandatory_skills = [ExtractedSkill(name=s, category="technical") for s in body.key_skills] or [
                ExtractedSkill(name="Financial Modeling", category="technical"),
                ExtractedSkill(name="Accounting", category="technical")
            ]
            good_to_have_skills = [
                ExtractedSkill(name="ERP Software (SAP/Oracle)", category="tools"),
                ExtractedSkill(name="Excel Advanced (VBA/Macros)", category="tools")
            ]
        else:
            # Default / Engineering
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
            min_exp, max_exp = 3.0, 8.0
            edu_req = "Bachelor's in Computer Science or equivalent"
            min_sal, max_sal = 120000.0, 180000.0
            mandatory_skills = [ExtractedSkill(name=s, category="technical") for s in body.key_skills] or [
                ExtractedSkill(name="Problem Solving", category="core"),
                ExtractedSkill(name="Software Design", category="technical")
            ]
            good_to_have_skills = [
                ExtractedSkill(name="CI/CD Pipelines", category="tools"),
                ExtractedSkill(name="Cloud Platforms (AWS/GCP)", category="tools")
            ]

    # Save a draft Job posting
    save_data = JobCreateSave(
        title=title,
        department=dept,
        raw_description=description,
        status=JobStatus.DRAFT,
        min_experience_years=min_exp,
        max_experience_years=max_exp,
        education_requirement=edu_req,
        location=loc,
        is_remote=body.is_remote,
        min_salary=min_sal,
        max_salary=max_sal,
        salary_currency=sal_curr,
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
