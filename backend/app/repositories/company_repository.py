import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.company import Company, SubscriptionPlan


class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, company_id: uuid.UUID) -> Optional[Company]:
        result = await self.db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Company]:
        result = await self.db.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, name: str, slug: str, domain: Optional[str] = None, plan: SubscriptionPlan = SubscriptionPlan.STARTER) -> Company:
        now = datetime.now(timezone.utc)
        company = Company(
            name=name,
            slug=slug,
            domain=domain,
            subscription_plan=plan,
            created_at=now,
            updated_at=now,
        )
        self.db.add(company)
        await self.db.flush()
        return company
