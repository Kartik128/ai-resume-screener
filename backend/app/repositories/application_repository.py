import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application import Application, ApplicationStatus


class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, application_id: uuid.UUID) -> Optional[Application]:
        stmt = (
            select(Application)
            .options(selectinload(Application.candidate), selectinload(Application.job))
            .where(Application.id == application_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID, recruiter_id: Optional[uuid.UUID] = None
    ) -> Application:
        stmt = select(Application).where(
            Application.job_id == job_id, Application.candidate_id == candidate_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        app = Application(
            job_id=job_id,
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            status=ApplicationStatus.APPLIED,
        )
        self.db.add(app)
        await self.db.flush()
        return app

    async def update_status(
        self, application_id: uuid.UUID, status: ApplicationStatus, notes: Optional[str] = None
    ) -> Application:
        app = await self.get_by_id(application_id)
        if app:
            app.status = status
            if notes is not None:
                app.notes = notes
            await self.db.flush()
        return app  # type: ignore

    async def list_by_job(
        self, job_id: uuid.UUID, status_filter: Optional[ApplicationStatus] = None
    ) -> Sequence[Application]:
        stmt = (
            select(Application)
            .options(selectinload(Application.candidate), selectinload(Application.job))
            .where(Application.job_id == job_id)
        )
        if status_filter:
            stmt = stmt.where(Application.status == status_filter)
        result = await self.db.execute(stmt)
        return result.scalars().all()
