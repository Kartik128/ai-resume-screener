import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).options(selectinload(User.company)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).options(selectinload(User.company)).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        company_id: uuid.UUID,
        role: UserRole = UserRole.RECRUITER,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            company_id=company_id,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        return await self.get_by_id(user.id)

    async def update_last_login(self, user_id: uuid.UUID) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.flush()
        return user

    async def get_all_by_company(self, company_id: uuid.UUID) -> Sequence[User]:
        stmt = (
            select(User)
            .options(selectinload(User.company))
            .where(User.company_id == company_id)
            .order_by(User.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
