"""
Assessments model — tracks customized micro-tests attached to a job opening
to validate skills through coding snippets or MCQ questions.
"""
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job


class Assessment(Base, UUIDMixin, TimestampMixin):
    """Factual questions validation micro-test set."""
    __tablename__ = "assessments"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    questions_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of MCQ questions
    time_limit_mins: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship("Job", lazy="joined")


class AssessmentResponse(Base, UUIDMixin, TimestampMixin):
    """Tracks replies and calculated test marks per candidate."""
    __tablename__ = "assessment_responses"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answers_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # mapping of {question_index: selected_choice_index}
    score: Mapped[float] = mapped_column(nullable=False)             # percentage validation score (0-100)

    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", lazy="joined")
