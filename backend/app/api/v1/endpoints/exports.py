import uuid
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.repositories.score_repository import ScoreRepository
from app.services.report_generator_service import ReportGeneratorService

router = APIRouter()


@router.get(
    "/job/{job_id}/csv",
    status_code=status.HTTP_200_OK,
    summary="Export candidate leaderboard to CSV file",
)
async def export_job_csv(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    score_repo = ScoreRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    scores = await score_repo.get_leaderboard_for_job(job_id)
    csv_content = ReportGeneratorService.generate_csv_report(job, scores)

    filename = f"candidates_{job.title.replace(' ', '_').lower()}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/job/{job_id}/excel",
    status_code=status.HTTP_200_OK,
    summary="Export candidate leaderboard to styled Excel (.xlsx) file",
)
async def export_job_excel(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    score_repo = ScoreRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    scores = await score_repo.get_leaderboard_for_job(job_id)
    excel_bytes = ReportGeneratorService.generate_excel_report(job, scores)

    filename = f"candidates_{job.title.replace(' ', '_').lower()}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/candidate/{candidate_id}/job/{job_id}/pdf",
    status_code=status.HTTP_200_OK,
    summary="Export executive PDF candidate assessment report",
)
async def export_candidate_pdf(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    score_repo = ScoreRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    score = await score_repo.get_by_job_and_candidate(job_id, candidate_id)
    if not score:
        raise NotFoundException(resource="Candidate Score", identifier=candidate_id)

    pdf_bytes = ReportGeneratorService.generate_pdf_report(job, score)
    filename = f"report_{score.candidate.full_name.replace(' ', '_').lower()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/compare",
    status_code=status.HTTP_200_OK,
    summary="Export candidate comparison matrix report to PDF",
)
async def export_comparison_pdf(
    job_id: uuid.UUID,
    candidate_ids: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.comparison_service import ComparisonService

    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    parsed_ids = [uuid.UUID(cid.strip()) for cid in candidate_ids.split(",") if cid.strip()]
    comparison_res = await ComparisonService.compare_candidates(
        job_id=job_id,
        candidate_ids=parsed_ids,
        company_id=current_user.company_id,
        db=db,
    )

    pdf_bytes = ReportGeneratorService.generate_comparison_pdf(job, comparison_res.columns)
    filename = f"comparison_{job.title.replace(' ', '_').lower()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
