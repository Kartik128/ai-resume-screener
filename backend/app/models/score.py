import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.candidate import Candidate
    from app.models.resume import Resume


class Score(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scores"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    mandatory_skills_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    nice_skills_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    industry_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    location_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    stability_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    certification_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    match_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job")
    candidate: Mapped["Candidate"] = relationship("Candidate")
    resume: Mapped["Resume"] = relationship("Resume")
