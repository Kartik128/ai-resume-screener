import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.candidate import Candidate, CandidateSkill
from app.models.skill import Skill
from app.schemas.resume import ResumeStructuredExtract


class CandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, candidate_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Candidate]:
        stmt = (
            select(Candidate)
            .options(
                selectinload(Candidate.resumes),
                selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill),
            )
            .where(Candidate.id == candidate_id, Candidate.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, company_id: uuid.UUID) -> Optional[Candidate]:
        stmt = (
            select(Candidate)
            .options(selectinload(Candidate.resumes))
            .where(Candidate.email == email.lower(), Candidate.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_from_parsed_dto(
        self,
        company_id: uuid.UUID,
        parsed: ResumeStructuredExtract,
        skills_map: Sequence[Skill],
    ) -> Candidate:
        candidate = None
        if parsed.email:
            candidate = await self.get_by_email(parsed.email, company_id)

        if not candidate:
            candidate = Candidate(
                company_id=company_id,
                full_name=parsed.name,
                email=parsed.email.lower() if parsed.email else None,
                phone=parsed.phone,
                location=parsed.location,
                linkedin_url=parsed.linkedin_url,
                github_url=parsed.github_url,
                portfolio_url=parsed.portfolio_url,
                total_experience_years=parsed.total_experience_years,
                raw_skills=[s.name for s in parsed.skills],
                summary=parsed.summary,
            )
            self.db.add(candidate)
            await self.db.flush()
        else:
            candidate.full_name = parsed.name
            candidate.phone = parsed.phone or candidate.phone
            candidate.location = parsed.location or candidate.location
            candidate.linkedin_url = parsed.linkedin_url or candidate.linkedin_url
            candidate.github_url = parsed.github_url or candidate.github_url
            candidate.portfolio_url = parsed.portfolio_url or candidate.portfolio_url
            candidate.total_experience_years = (
                parsed.total_experience_years or candidate.total_experience_years
            )
            candidate.raw_skills = [s.name for s in parsed.skills]
            candidate.summary = parsed.summary or candidate.summary
            await self.db.flush()

        # Link skills
        for s_entity in skills_map:
            cs = CandidateSkill(candidate_id=candidate.id, skill_id=s_entity.id)
            self.db.add(cs)

        await self.db.flush()
        return candidate
