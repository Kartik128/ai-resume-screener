import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.feedback import RecruiterAction, RecruiterFeedback


class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_feedback(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        recruiter_id: uuid.UUID,
        action: RecruiterAction,
        rating: Optional[float] = None,
        feedback_text: Optional[str] = None,
    ) -> RecruiterFeedback:
        fb = RecruiterFeedback(
            job_id=job_id,
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            action=action,
            rating=rating,
            feedback_text=feedback_text,
            weight_adjustments={"learned": True, "action": action.value},
        )
        self.db.add(fb)
        await self.db.flush()
        return fb

    async def list_by_job(self, job_id: uuid.UUID) -> Sequence[RecruiterFeedback]:
        stmt = select(RecruiterFeedback).where(RecruiterFeedback.job_id == job_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
