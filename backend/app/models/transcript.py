"""
Interview Intelligence Models. Schemas for holding interview audio transcripts and score matching logs.
"""
import uuid
from sqlalchemy import String, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class InterviewTranscript(Base, UUIDMixin, TimestampMixin):
    """Holds transcribing texts and scorecard alignment values for candidate interviews."""
    __tablename__ = "interview_transcripts"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    summary_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    alignment_score: Mapped[float] = mapped_column(Float, default=100.0)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", lazy="joined")
    job: Mapped["Job"] = relationship("Job", lazy="joined")
