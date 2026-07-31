import mimetypes
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
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

    # 5. Check Duplicate Candidates
    from app.services.duplicate_detector_service import DuplicateDetectorService
    is_dup, canonical_id, confidence = await DuplicateDetectorService.check_duplicate(
        company_id=current_user.company_id,
        email=parsed_dto.email,
        phone=parsed_dto.phone,
        name=parsed_dto.name,
        location=parsed_dto.location,
        db=db,
    )

    # 6. Create or Update Candidate
    candidate = await candidate_repo.create_or_update_from_parsed_dto(
        company_id=current_user.company_id,
        parsed=parsed_dto,
        skills_map=skill_entities,
    )

    # 7. Save Resume Record
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

    # Save link if duplicate is found and it is not matching itself
    if is_dup and canonical_id != candidate.id:
        await DuplicateDetectorService.save_duplicate_link(
            canonical_id=canonical_id,
            duplicate_id=candidate.id,
            confidence=confidence,
            db=db,
        )

    out = ResumeRead.model_validate(resume)
    out.is_duplicate = is_dup if (is_dup and canonical_id != candidate.id) else False
    out.duplicate_candidate_id = canonical_id if (is_dup and canonical_id != candidate.id) else None
    out.duplicate_confidence = confidence if (is_dup and canonical_id != candidate.id) else None
    return out


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

            # Check duplicates
            from app.services.duplicate_detector_service import DuplicateDetectorService
            is_dup, canonical_id, confidence = await DuplicateDetectorService.check_duplicate(
                company_id=current_user.company_id,
                email=parsed_dto.email,
                phone=parsed_dto.phone,
                name=parsed_dto.name,
                location=parsed_dto.location,
                db=db,
            )

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

            if is_dup and canonical_id != candidate.id:
                await DuplicateDetectorService.save_duplicate_link(
                    canonical_id=canonical_id,
                    duplicate_id=candidate.id,
                    confidence=confidence,
                    db=db,
                )

            res_dto = ResumeRead.model_validate(resume)
            res_dto.is_duplicate = is_dup if (is_dup and canonical_id != candidate.id) else False
            res_dto.duplicate_candidate_id = canonical_id if (is_dup and canonical_id != candidate.id) else None
            res_dto.duplicate_confidence = confidence if (is_dup and canonical_id != candidate.id) else None

            successful_resumes.append(res_dto)
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


@router.get(
    "/{resume_id}/file",
    status_code=status.HTTP_200_OK,
    summary="Download or view the original uploaded resume file (PDF, DOCX, TXT)",
)
async def download_resume_file(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream the original uploaded resume file back to the client.
    Supports PDF, DOCX, and TXT. The file is served inline for PDF
    (so browsers can display it) and as attachment for other formats.
    """
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get_by_id(resume_id)
    if not resume:
        raise NotFoundException(resource="Resume", identifier=resume_id)

    file_path = Path(resume.file_path) if resume.file_path else None

    # If the physical file exists on disk, serve it directly
    if file_path and file_path.exists():
        media_type = resume.file_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        filename = resume.file_name or file_path.name

        # PDFs and text → inline (browser-viewable); everything else → attachment download
        disposition = "inline" if media_type in ("application/pdf", "text/plain") else "attachment"

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
        )

    # Fallback: file was not stored on disk (e.g. in-memory upload for tests)
    # Serve the raw extracted text as a downloadable .txt file
    raw_text = resume.raw_text or "(No resume text available)"
    filename = (resume.file_name or "resume").replace(".pdf", "").replace(".docx", "") + ".txt"

    from fastapi.responses import Response
    return Response(
        content=raw_text.encode("utf-8"),
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(raw_text.encode("utf-8"))),
        },
    )


@router.get(
    "/{resume_id}/preview",
    status_code=status.HTTP_200_OK,
    summary="Get resume structured preview data for in-app viewer (text + parsed info)",
)
async def get_resume_preview(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the resume's raw text and parsed structured data for rendering
    a rich in-browser preview without needing to download the file.
    """
    resume_repo = ResumeRepository(db)
    resume = await resume_repo.get_by_id(resume_id)
    if not resume:
        raise NotFoundException(resource="Resume", identifier=resume_id)

    parsed = resume.parsed_data or {}
    file_path = Path(resume.file_path) if resume.file_path else None
    file_exists = file_path and file_path.exists()

    return JSONResponse({
        "resume_id": str(resume.id),
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "file_size_bytes": resume.file_size_bytes,
        "file_available": bool(file_exists),
        "candidate_name": parsed.get("name", ""),
        "email": parsed.get("email", ""),
        "phone": parsed.get("phone", ""),
        "location": parsed.get("location", ""),
        "linkedin_url": parsed.get("linkedin_url", ""),
        "github_url": parsed.get("github_url", ""),
        "total_experience_years": parsed.get("total_experience_years", 0),
        "summary": parsed.get("summary", ""),
        "skills": [s.get("name", s) if isinstance(s, dict) else s for s in parsed.get("skills", [])],
        "certifications": [c.get("name", c) if isinstance(c, dict) else c for c in parsed.get("certifications", [])],
        "achievements": parsed.get("achievements", []),
        "work_experience": parsed.get("work_experience", []),
        "education": parsed.get("education", []),
        "raw_text": resume.raw_text or "",
        "download_url": f"/api/v1/resumes/{resume_id}/file",
    })


@router.delete(
    "/candidate/{candidate_id}",
    status_code=status.HTTP_200_OK,
    summary="GDPR Right to Deletion: permanently wipe all candidate records, parse text, scores, and files",
)
async def delete_candidate_gdpr(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.candidate import Candidate
    from app.models.resume import Resume
    from app.models.application import Application
    from app.models.score import Score
    from sqlalchemy import delete

    # Verify candidate tenant ownership
    check_cand = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.company_id == current_user.company_id)
    )
    candidate = check_cand.scalar_one_or_none()
    if not candidate:
        raise NotFoundException(resource="Candidate", identifier=candidate_id)

    # 1. Fetch file paths to wipe from local storage/disk
    res_res = await db.execute(select(Resume).where(Resume.candidate_id == candidate_id))
    resumes = res_res.scalars().all()
    for r in resumes:
        if r.file_path and os.path.exists(r.file_path):
            try:
                os.remove(r.file_path)
            except Exception as e:
                logger.error(f"Failed to delete resume file path: {r.file_path}. Error: {e}")

    # 2. Cascade delete database entities
    await db.execute(delete(Score).where(Score.resume_id.in_([r.id for r in resumes])))
    await db.execute(delete(Application).where(Application.candidate_id == candidate_id))
    await db.execute(delete(Resume).where(Resume.candidate_id == candidate_id))
    await db.execute(delete(Candidate).where(Candidate.id == candidate_id))
    
    await db.commit()
    return {"success": True, "detail": "Candidate wiped successfully for GDPR compliance."}
