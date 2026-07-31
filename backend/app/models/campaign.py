import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin, GUID

class CampaignTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaign_templates"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False) # "email" or "whatsapp"
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
