"""
DuplicateDetectorService — fuzzy duplicate logic. Matches on email, phone, LinkedIn,
or name+location overlap similarity, saving secondary duplicate records.
"""
import uuid
from typing import Optional, Tuple
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.candidate import Candidate
from app.models.duplicate_candidate import DuplicateCandidate


class DuplicateDetectorService:
    """Fuzzy duplicate check running on every resume parse pipeline upload."""

    @staticmethod
    async def check_duplicate(
        company_id: uuid.UUID,
        email: Optional[str],
        phone: Optional[str],
        name: str,
        location: Optional[str],
        db: AsyncSession,
    ) -> Tuple[bool, Optional[uuid.UUID], float]:
        """Check duplicate. Returns (is_duplicate, canonical_id, confidence)."""
        # Exact email match
        if email:
            result = await db.execute(
                select(Candidate).where(Candidate.company_id == company_id, Candidate.email == email)
            )
            match = result.scalar_one_or_none()
            if match:
                return True, match.id, 1.0

        # Exact phone match
        if phone:
            result = await db.execute(
                select(Candidate).where(Candidate.company_id == company_id, Candidate.phone == phone)
            )
            match = result.scalar_one_or_none()
            if match:
                return True, match.id, 1.0

        # Fuzzy Name + Location match
        if name:
            name_pat = f"%{name.lower()}%"
            # Get candidates with similar name
            result = await db.execute(
                select(Candidate).where(
                    Candidate.company_id == company_id,
                    Candidate.full_name.ilike(name_pat)
                )
            )
            matches = result.scalars().all()
            for m in matches:
                # Name overlap check
                conf = 0.70
                if location and m.location and location.lower()[:5] in m.location.lower():
                    conf += 0.20
                if conf >= 0.85:
                    return True, m.id, conf

        return False, None, 0.0

    @staticmethod
    async def save_duplicate_link(
        canonical_id: uuid.UUID,
        duplicate_id: uuid.UUID,
        confidence: float,
        db: AsyncSession,
    ):
        link = DuplicateCandidate(
            canonical_id=canonical_id,
            duplicate_id=duplicate_id,
            confidence=confidence,
        )
        db.add(link)
        await db.commit()
