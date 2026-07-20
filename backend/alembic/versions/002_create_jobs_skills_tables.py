"""create jobs and skills tables

Revision ID: 002_create_jobs_skills_tables
Revises: 001_create_tenant_user_tables
Create Date: 2026-07-20 15:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "002_create_jobs_skills_tables"
down_revision: Union[str, None] = "001_create_tenant_user_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create skills table
    op.create_table(
        "skills",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("synonyms", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_skills_category"), "skills", ["category"], unique=False)
    op.create_index(op.f("ix_skills_id"), "skills", ["id"], unique=False)
    op.create_index(op.f("ix_skills_name"), "skills", ["name"], unique=True)

    # 2. Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("company_id", GUID(), nullable=False),
        sa.Column("creator_id", GUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "ACTIVE", "PAUSED", "CLOSED", name="jobstatus"), nullable=False),
        sa.Column("min_experience_years", sa.Float(), nullable=True),
        sa.Column("max_experience_years", sa.Float(), nullable=True),
        sa.Column("education_requirement", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("min_salary", sa.Float(), nullable=True),
        sa.Column("max_salary", sa.Float(), nullable=True),
        sa.Column("salary_currency", sa.String(length=10), nullable=True),
        sa.Column("responsibilities", sa.JSON(), nullable=True),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_company_id"), "jobs", ["company_id"], unique=False)
    op.create_index(op.f("ix_jobs_creator_id"), "jobs", ["creator_id"], unique=False)
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)
    op.create_index(op.f("ix_jobs_title"), "jobs", ["title"], unique=False)

    # 3. Create job_skills table
    op.create_table(
        "job_skills",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("skill_id", GUID(), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("min_experience_years", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_skills_id"), "job_skills", ["id"], unique=False)
    op.create_index(op.f("ix_job_skills_job_id"), "job_skills", ["job_id"], unique=False)
    op.create_index(op.f("ix_job_skills_skill_id"), "job_skills", ["skill_id"], unique=False)


def downgrade() -> None:
    op.drop_table("job_skills")
    op.drop_table("jobs")
    op.drop_table("skills")
    op.execute("DROP TYPE IF EXISTS jobstatus")
