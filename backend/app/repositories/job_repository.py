import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobSkill, JobStatus
from app.models.skill import Skill
from app.schemas.job import JobCreateSave


class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Job]:
        stmt = (
            select(Job)
            .options(
                selectinload(Job.job_skills).selectinload(JobSkill.skill)
            )
            .where(Job.id == job_id, Job.company_id == company_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(self, company_id: uuid.UUID) -> Sequence[Job]:
        stmt = (
            select(Job)
            .options(
                selectinload(Job.job_skills).selectinload(JobSkill.skill)
            )
            .where(Job.company_id == company_id)
            .order_by(Job.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_job_with_skills(
        self,
        company_id: uuid.UUID,
        creator_id: uuid.UUID,
        data: JobCreateSave,
        mandatory_skill_entities: Sequence[Skill],
        good_skill_entities: Sequence[Skill],
    ) -> Job:
        job = Job(
            company_id=company_id,
            creator_id=creator_id,
            title=data.title,
            department=data.department,
            raw_description=data.raw_description,
            status=data.status,
            min_experience_years=data.min_experience_years,
            max_experience_years=data.max_experience_years,
            education_requirement=data.education_requirement,
            location=data.location,
            is_remote=data.is_remote,
            min_salary=data.min_salary,
            max_salary=data.max_salary,
            salary_currency=data.salary_currency,
            responsibilities=data.responsibilities,
            parsed_data={
                "mandatory_skills": [s.name for s in mandatory_skill_entities],
                "good_to_have_skills": [s.name for s in good_skill_entities],
            },
        )
        self.db.add(job)
        await self.db.flush()

        # Add JobSkills
        for skill in mandatory_skill_entities:
            js = JobSkill(
                job_id=job.id,
                skill_id=skill.id,
                is_mandatory=True,
                weight=1.5,
            )
            self.db.add(js)

        for skill in good_skill_entities:
            js = JobSkill(
                job_id=job.id,
                skill_id=skill.id,
                is_mandatory=False,
                weight=1.0,
            )
            self.db.add(js)

        await self.db.flush()
        # Reload relationships
        return await self.get_by_id(job.id, company_id)  # type: ignore
