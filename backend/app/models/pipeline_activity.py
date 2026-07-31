"""
PipelineActivity model — immutable audit log of every stage transition,
note, or action taken on a candidate application.
"""
import enum
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.user import User


class ActivityType(str, enum.Enum):
    STAGE_CHANGE = "stage_change"
    NOTE_ADDED = "note_added"
    OWNER_ASSIGNED = "owner_assigned"
    REMINDER_SET = "reminder_set"
    IDENTITY_REVEALED = "identity_revealed"   # blind mode audit
    SCORE_OVERRIDDEN = "score_overridden"      # score override audit


class PipelineActivity(Base, UUIDMixin, TimestampMixin):
    """Immutable event log — one row per action on an application."""
    __tablename__ = "pipeline_activities"

    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    activity_type: Mapped[ActivityType] = mapped_column(
        SQLEnum(ActivityType), nullable=False, index=True
    )
    from_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # e.g. old stage
    to_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # e.g. new stage
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)                # free-text note

    # Relationships
    application: Mapped["Application"] = relationship("Application", lazy="joined")
    actor: Mapped[Optional["User"]] = relationship("User", lazy="joined")
