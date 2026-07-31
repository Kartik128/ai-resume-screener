import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.models.user import User


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    MAYBE = "maybe"
    REJECTED = "rejected"
    INTERVIEWED = "interviewed"
    OFFER_RELEASED = "offer_released"
    JOINED = "joined"


class Application(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "applications"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Pipeline owner (who is responsible for progressing this candidate)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # When the stage last changed (for time-to-hire analytics)
    stage_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Recruiter reminder
    reminder_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reminder_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job")
    candidate: Mapped["Candidate"] = relationship("Candidate")
    recruiter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[recruiter_id])
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
