"""
Offer letters database model. Schemas for generating and sending offer documents with salary details.
"""
import uuid
from sqlalchemy import String, ForeignKey, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class OfferLetter(Base, UUIDMixin, TimestampMixin):
    """Enables recruiters to generate and track offer letter releases and e-signatures."""
    __tablename__ = "offer_letters"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    equity_grants: Mapped[str] = mapped_column(String(255), nullable=True)
    sign_status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False) # 'sent' | 'signed'

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", lazy="joined")
    job: Mapped["Job"] = relationship("Job", lazy="joined")
