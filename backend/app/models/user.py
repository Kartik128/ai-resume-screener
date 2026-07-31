import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.audit import AuditLog


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.RECRUITER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    google_access_token: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    google_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    mail_provider: Mapped[str] = mapped_column(String(50), default="smtp", nullable=False)
    microsoft_access_token: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    microsoft_refresh_token: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    microsoft_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="users", lazy="joined")
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
