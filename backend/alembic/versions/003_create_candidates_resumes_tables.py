"""create candidates and resumes tables

Revision ID: 003_create_candidates_resumes_tables
Revises: 002_create_jobs_skills_tables
Create Date: 2026-07-20 15:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "003_create_candidates_resumes_tables"
down_revision: Union[str, None] = "002_create_jobs_skills_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create candidates table
    op.create_table(
        "candidates",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("company_id", GUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("portfolio_url", sa.String(length=500), nullable=True),
        sa.Column("total_experience_years", sa.Float(), nullable=True),
        sa.Column("raw_skills", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidates_company_id"), "candidates", ["company_id"], unique=False)
    op.create_index(op.f("ix_candidates_email"), "candidates", ["email"], unique=False)
    op.create_index(op.f("ix_candidates_full_name"), "candidates", ["full_name"], unique=False)
    op.create_index(op.f("ix_candidates_id"), "candidates", ["id"], unique=False)

    # 2. Create candidate_skills table
    op.create_table(
        "candidate_skills",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("candidate_id", GUID(), nullable=False),
        sa.Column("skill_id", GUID(), nullable=False),
        sa.Column("experience_years", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_candidate_skills_candidate_id"), "candidate_skills", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_candidate_skills_id"), "candidate_skills", ["id"], unique=False)
    op.create_index(op.f("ix_candidate_skills_skill_id"), "candidate_skills", ["skill_id"], unique=False)

    # 3. Create resumes table
    op.create_table(
        "resumes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("candidate_id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column("parsing_status", sa.Enum("PENDING", "PROCESSING", "PARSED", "FAILED", name="parsingstatus"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_candidate_id"), "resumes", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_resumes_id"), "resumes", ["id"], unique=False)
    op.create_index(op.f("ix_resumes_job_id"), "resumes", ["job_id"], unique=False)
    op.create_index(op.f("ix_resumes_parsing_status"), "resumes", ["parsing_status"], unique=False)


def downgrade() -> None:
    op.drop_table("resumes")
    op.drop_table("candidate_skills")
    op.drop_table("candidates")
    op.execute("DROP TYPE IF EXISTS parsingstatus")
