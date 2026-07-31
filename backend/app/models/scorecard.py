"""
Scorecard model — stores recruiter-customized scoring weights per job.
Each job can have one scorecard. If none exists the scoring engine uses defaults.
"""
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Scorecard(Base, UUIDMixin, TimestampMixin):
    """Recruiter-defined scoring dimension weights for a specific job."""
    __tablename__ = "scorecards"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Weights (must sum to 100). Stored as floats for precision.
    w_mandatory_skills: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    w_experience: Mapped[float] = mapped_column(Float, default=20.0, nullable=False)
    w_nice_to_have: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    w_career_stability: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    w_industry_match: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    w_education: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    w_certifications: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    w_location: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)

    # Optional per-dimension custom labels / criteria notes
    criteria_notes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", lazy="joined")
    creator: Mapped[Optional["User"]] = relationship("User", lazy="joined")
