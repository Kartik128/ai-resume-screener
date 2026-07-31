"""
ScoreOverride model — tracks manual rating adjustments made by recruiters
with details on original value, new value, who adjusted it, and the mandatory explanation.
"""
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.score import Score
    from app.models.user import User


class ScoreOverride(Base, UUIDMixin, TimestampMixin):
    """Audit log of manual recruiter overrides applied to candidate scores."""
    __tablename__ = "score_overrides"

    score_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("scores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'mandatory_skills'
    original_value: Mapped[float] = mapped_column(Float, nullable=False)
    new_value: Mapped[float] = mapped_column(Float, nullable=False)
    overridden_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    score: Mapped["Score"] = relationship("Score", lazy="joined")
    actor: Mapped[Optional["User"]] = relationship("User", lazy="joined")
