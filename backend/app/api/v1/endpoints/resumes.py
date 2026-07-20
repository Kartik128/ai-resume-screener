import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.candidate import CandidateRead
from app.schemas.resume import BulkUploadResponse, ResumeRead
from app.services.resume_extractor_service import ResumeExtractorService
from app.services.resume_parser_service import ResumeParserService
from app.services.storage_service import StorageService

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload single resume, extract text via PyMuPDF/OCR, parse structured AI JSON and save",
)
async def upload_resume(
    file: UploadFile = File(...),
    job_id: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeRead:
    skill_repo = SkillRepository(db)
    candidate_repo = CandidateRepository(db)
    resume_repo = ResumeRepository(db)

    # 1. Store File locally/S3
    saved_file_path = await StorageService.save_resume_file(current_user.company_id, file)

    # 2. Extract Raw Text (PDF, DOCX, OCR Image)
    raw_text = await ResumeExtractorService.extract_raw_text(file)

    # 3. AI Parse Structured JSON
    parsed_dto = await ResumeParserService.parse_resume_text(raw_text)

    # 4. Save/Update Normalized Skill Entities
    skill_entities = []
    for sk in parsed_dto.skills:
        s_ent = await skill_repo.get_or_create(name=sk.name, category=sk.category)
        skill_entities.append(s_ent)

    # 5. Create or Update Candidate
    candidate = await candidate_repo.create_or_update_from_parsed_dto(
        company_id=current_user.company_id,
        parsed=parsed_dto,
        skills_map=skill_entities,
    )

    # 6. Save Resume Record
    file_bytes = await file.read()
    resume = await resume_repo.create(
        candidate_id=candidate.id,
        job_id=job_id,
        file_name=file.filename or "resume.pdf",
        file_path=saved_file_path,
        file_type=file.content_type or "application/pdf",
        file_size_bytes=len(file_bytes),
        raw_text=raw_text,
        parsed_dto=parsed_dto,
    )

    return ResumeRead.model_validate(resume)


@router.post(
    "/bulk-upload",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk upload up to 50 resumes for a Job Posting",
)
async def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    job_id: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BulkUploadResponse:
    successful_resumes = []
    failed_count = 0

    for file in files:
        try:
            skill_repo = SkillRepository(db)
            candidate_repo = CandidateRepository(db)
            resume_repo = ResumeRepository(db)

            saved_file_path = await StorageService.save_resume_file(current_user.company_id, file)
            raw_text = await ResumeExtractorService.extract_raw_text(file)
            parsed_dto = await ResumeParserService.parse_resume_text(raw_text)

            skill_entities = []
            for sk in parsed_dto.skills:
                s_ent = await skill_repo.get_or_create(name=sk.name, category=sk.category)
                skill_entities.append(s_ent)

            candidate = await candidate_repo.create_or_update_from_parsed_dto(
                company_id=current_user.company_id,
                parsed=parsed_dto,
                skills_map=skill_entities,
            )

            file_bytes = await file.read()
            resume = await resume_repo.create(
                candidate_id=candidate.id,
                job_id=job_id,
                file_name=file.filename or "resume.pdf",
                file_path=saved_file_path,
                file_type=file.content_type or "application/pdf",
                file_size_bytes=len(file_bytes),
                raw_text=raw_text,
                parsed_dto=parsed_dto,
            )

            successful_resumes.append(ResumeRead.model_validate(resume))
        except Exception as e:
            logger.error(f"Failed bulk resume upload for file '{file.filename}': {str(e)}")
            failed_count += 1

    return BulkUploadResponse(
        total_uploaded=len(files),
        successful_count=len(successful_resumes),
        failed_count=failed_count,
        resumes=successful_resumes,
    )


@router.get(
    "/candidate/{candidate_id}",
    response_model=CandidateRead,
    status_code=status.HTTP_200_OK,
    summary="Get candidate profile and uploaded resumes",
)
async def get_candidate_profile(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateRead:
    candidate_repo = CandidateRepository(db)
    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate:
        raise NotFoundException(resource="Candidate", identifier=candidate_id)
    return CandidateRead.model_validate(candidate)


@router.get(
    "/job/{job_id}",
    response_model=List[ResumeRead],
    status_code=status.HTTP_200_OK,
    summary="List all uploaded resumes for a specific job posting",
)
async def list_resumes_for_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ResumeRead]:
    resume_repo = ResumeRepository(db)
    resumes = await resume_repo.list_by_job(job_id)
    return [ResumeRead.model_validate(r) for r in resumes]
