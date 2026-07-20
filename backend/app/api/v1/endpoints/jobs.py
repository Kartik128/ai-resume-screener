import uuid
from typing import List
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
