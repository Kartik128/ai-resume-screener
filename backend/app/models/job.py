import enum
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import String, Text, Float, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User
    from app.models.skill import Skill
    from app.models.comment import JobComment


class JobStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class Job(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "jobs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), default=JobStatus.ACTIVE, nullable=False, index=True
    )

    # Requirements extracted/edited
    min_experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education_requirement: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blind_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Hides PII during initial scoring

    # Compensation
    min_salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), default="USD", nullable=True)

    # Detailed structured extractions
    responsibilities: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    parsed_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="joined")
    creator: Mapped["User"] = relationship("User", lazy="joined")
    job_skills: Mapped[List["JobSkill"]] = relationship(
        "JobSkill", back_populates="job", cascade="all, delete-orphan", lazy="selectin"
    )
    comments: Mapped[List["JobComment"]] = relationship(
        "JobComment", back_populates="job", cascade="all, delete-orphan", lazy="selectin"
    )


class JobSkill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    min_experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="job_skills", lazy="joined")
