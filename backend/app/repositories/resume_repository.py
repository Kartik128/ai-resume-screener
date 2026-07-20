import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import ParsingStatus, Resume
from app.schemas.resume import ResumeStructuredExtract


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, resume_id: uuid.UUID) -> Optional[Resume]:
        stmt = (
            select(Resume)
            .options(selectinload(Resume.candidate))
            .where(Resume.id == resume_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        candidate_id: uuid.UUID,
        job_id: Optional[uuid.UUID],
        file_name: str,
        file_path: str,
        file_type: str,
        file_size_bytes: int,
        raw_text: str,
        parsed_dto: ResumeStructuredExtract,
    ) -> Resume:
        resume = Resume(
            candidate_id=candidate_id,
            job_id=job_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            raw_text=raw_text,
            parsed_data=parsed_dto.model_dump(),
            parsing_status=ParsingStatus.PARSED,
        )
        self.db.add(resume)
        await self.db.flush()
        return resume

    async def list_by_job(self, job_id: uuid.UUID) -> Sequence[Resume]:
        stmt = (
            select(Resume)
            .options(selectinload(Resume.candidate))
            .where(Resume.job_id == job_id)
            .order_by(Resume.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
