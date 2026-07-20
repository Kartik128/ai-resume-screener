import uuid
from typing import TYPE_CHECKING, Any, Dict
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company


class Setting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "settings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="settings")
