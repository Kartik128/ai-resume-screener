import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.score import Score
from app.schemas.scoring import ScoreBreakdownResponse


class ScoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_job_and_candidate(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Optional[Score]:
        stmt = (
            select(Score)
            .options(selectinload(Score.candidate), selectinload(Score.resume))
            .where(Score.job_id == job_id, Score.candidate_id == candidate_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_or_update_score(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        resume_id: uuid.UUID,
        breakdown: ScoreBreakdownResponse,
    ) -> Score:
        existing = await self.get_by_job_and_candidate(job_id, candidate_id)
        if not existing:
            score = Score(
                job_id=job_id,
                candidate_id=candidate_id,
                resume_id=resume_id,
                overall_score=breakdown.overall_score,
                mandatory_skills_score=breakdown.mandatory_skills.raw_score,
                nice_skills_score=breakdown.nice_to_have_skills.raw_score,
                experience_score=breakdown.experience.raw_score,
                education_score=breakdown.education.raw_score,
                industry_score=breakdown.industry_match.raw_score,
                location_score=breakdown.location.raw_score,
                stability_score=breakdown.career_stability.raw_score,
                certification_score=breakdown.certifications.raw_score,
                semantic_similarity=breakdown.mandatory_skills.raw_score / 100.0,
                match_breakdown=breakdown.model_dump(),
            )
            self.db.add(score)
            await self.db.flush()
            return score
        else:
            existing.overall_score = breakdown.overall_score
            existing.mandatory_skills_score = breakdown.mandatory_skills.raw_score
            existing.nice_skills_score = breakdown.nice_to_have_skills.raw_score
            existing.experience_score = breakdown.experience.raw_score
            existing.education_score = breakdown.education.raw_score
            existing.industry_score = breakdown.industry_match.raw_score
            existing.location_score = breakdown.location.raw_score
            existing.stability_score = breakdown.career_stability.raw_score
            existing.certification_score = breakdown.certifications.raw_score
            existing.semantic_similarity = breakdown.mandatory_skills.raw_score / 100.0
            existing.match_breakdown = breakdown.model_dump()
            await self.db.flush()
            return existing

    async def get_leaderboard_for_job(self, job_id: uuid.UUID) -> Sequence[Score]:
        stmt = (
            select(Score)
            .options(selectinload(Score.candidate), selectinload(Score.resume))
            .where(Score.job_id == job_id)
            .order_by(Score.overall_score.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
