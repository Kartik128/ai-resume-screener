"""create applications and feedback tables

Revision ID: 005_create_applications_feedback_tables
Revises: 004_create_scores_table
Create Date: 2026-07-20 15:08:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "005_create_applications_feedback_tables"
down_revision: Union[str, None] = "004_create_scores_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create applications table
    op.create_table(
        "applications",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("candidate_id", GUID(), nullable=False),
        sa.Column("recruiter_id", GUID(), nullable=True),
        sa.Column("status", sa.Enum("APPLIED", "SHORTLISTED", "MAYBE", "REJECTED", "INTERVIEWED", "OFFER_RELEASED", "JOINED", name="applicationstatus"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_candidate_id"), "applications", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_applications_id"), "applications", ["id"], unique=False)
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"], unique=False)
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)

    # 2. Create recruiter_feedback table
    op.create_table(
        "recruiter_feedback",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("candidate_id", GUID(), nullable=False),
        sa.Column("recruiter_id", GUID(), nullable=False),
        sa.Column("action", sa.Enum("SHORTLISTED", "REJECTED", "INTERVIEWED", "SELECTED", "OFFER_RELEASED", "JOINED", name="recruiteraction"), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("weight_adjustments", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recruiter_feedback_action"), "recruiter_feedback", ["action"], unique=False)
    op.create_index(op.f("ix_recruiter_feedback_candidate_id"), "recruiter_feedback", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_recruiter_feedback_id"), "recruiter_feedback", ["id"], unique=False)
    op.create_index(op.f("ix_recruiter_feedback_job_id"), "recruiter_feedback", ["job_id"], unique=False)
    op.create_index(op.f("ix_recruiter_feedback_recruiter_id"), "recruiter_feedback", ["recruiter_id"], unique=False)


def downgrade() -> None:
    op.drop_table("recruiter_feedback")
    op.drop_table("applications")
    op.execute("DROP TYPE IF EXISTS recruiteraction")
    op.execute("DROP TYPE IF EXISTS applicationstatus")
