"""
Webhook models and settings configurations. Exposes integration registration hooks.
"""
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company


class WebhookSubscription(Base, UUIDMixin, TimestampMixin):
    """Enables integration partners to subscribe to candidate pipeline stage updates."""
    __tablename__ = "webhook_subscriptions"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), default="candidate.stage_changed", nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="joined")
