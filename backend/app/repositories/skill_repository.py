import uuid
from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.skill import Skill


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[Skill]:
        stmt = select(Skill).where(Skill.name.ilike(name.strip()))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, name: str, category: Optional[str] = None, synonyms: Optional[List[str]] = None) -> Skill:
        name_clean = name.strip()
        existing = await self.get_by_name(name_clean)
        if existing:
            return existing

        skill = Skill(
            name=name_clean,
            category=category,
            synonyms=synonyms or [],
        )
        self.db.add(skill)
        await self.db.flush()
        return skill
