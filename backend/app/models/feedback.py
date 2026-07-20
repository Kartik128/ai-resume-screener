import enum
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Float, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.models.user import User


class RecruiterAction(str, enum.Enum):
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    INTERVIEWED = "interviewed"
    SELECTED = "selected"
    OFFER_RELEASED = "offer_released"
    JOINED = "joined"


class RecruiterFeedback(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "recruiter_feedback"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[RecruiterAction] = mapped_column(
        SQLEnum(RecruiterAction), nullable=False, index=True
    )
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight_adjustments: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job")
    candidate: Mapped["Candidate"] = relationship("Candidate")
    recruiter: Mapped["User"] = relationship("User")
