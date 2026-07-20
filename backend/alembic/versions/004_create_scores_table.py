"""create scores table

Revision ID: 004_create_scores_table
Revises: 003_create_candidates_resumes_tables
Create Date: 2026-07-20 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "004_create_scores_table"
down_revision: Union[str, None] = "003_create_candidates_resumes_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scores",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("candidate_id", GUID(), nullable=False),
        sa.Column("resume_id", GUID(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("mandatory_skills_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("nice_skills_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("experience_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("education_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("industry_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("location_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("stability_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("certification_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("semantic_similarity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("match_breakdown", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scores_candidate_id"), "scores", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_scores_id"), "scores", ["id"], unique=False)
    op.create_index(op.f("ix_scores_job_id"), "scores", ["job_id"], unique=False)
    op.create_index(op.f("ix_scores_overall_score"), "scores", ["overall_score"], unique=False)
    op.create_index(op.f("ix_scores_resume_id"), "scores", ["resume_id"], unique=False)


def downgrade() -> None:
    op.drop_table("scores")
