import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class JobComment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "job_comments"

    job_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="comments", lazy="joined")
    user: Mapped["User"] = relationship("User", lazy="joined")
