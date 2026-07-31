"""
DuplicateCandidate link model — maps a duplicate candidate profile to
their canonical (primary) candidate record.
"""
import uuid
from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin


class DuplicateCandidate(Base, UUIDMixin, TimestampMixin):
    """Tracks fuzzy candidate duplication link mappings."""
    __tablename__ = "duplicate_candidates"

    canonical_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    duplicate_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
