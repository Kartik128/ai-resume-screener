"""
Governance & GDPR Compliance API.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


@router.post("/gdpr/erase/{candidate_id}")
async def gdpr_erase_candidate(
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GDPR Right-to-Erasure: permanently delete all data for a candidate.
    Requires admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may trigger GDPR erasure.",
        )

    # Cross-tenant data boundary verification:
    cand_check = await db.execute(
        text("SELECT company_id FROM candidates WHERE id = :cid"),
        {"cid": str(candidate_id)}
    )
    row = cand_check.fetchone()
    if not row or str(row[0]) != str(current_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Candidate belongs to a different organization"
        )

    # Child tables first, then the root candidates table
    # Deleting score_overrides requires a subquery or join as it doesn't have a direct candidate_id column
    await db.execute(
        text("DELETE FROM score_overrides WHERE score_id IN (SELECT id FROM scores WHERE candidate_id = :cid)"),
        {"cid": str(candidate_id)}
    )

    tables_to_clear = [
        "quality_of_hire_reviews",
        "offer_letters",
        "assessment_responses",
        "candidate_experience_feedback",
        "interview_transcripts",
        "scores",
        "applications",
        "candidates",
    ]

    for table in tables_to_clear:
        if table == "candidates":
            await db.execute(
                text(f"DELETE FROM {table} WHERE id = :cid"),
                {"cid": str(candidate_id)},
            )
        else:
            await db.execute(
                text(f"DELETE FROM {table} WHERE candidate_id = :cid"),
                {"cid": str(candidate_id)},
            )

    await db.commit()

    return {
        "erased": True,
        "candidate_id": str(candidate_id),
        "tables_cleared": tables_to_clear,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/data-retention/summary")
async def data_retention_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a data-retention summary for all candidates belonging to the
    current user's company, broken down by age thresholds.
    """
    cid = str(current_user.company_id)

    total_result = await db.execute(
        text("SELECT COUNT(*) FROM candidates WHERE company_id = :cid"),
        {"cid": cid},
    )
    total_candidates = total_result.scalar() or 0

    r90 = await db.execute(
        text(
            "SELECT COUNT(*) FROM candidates "
            "WHERE company_id = :cid "
            "AND julianday('now') - julianday(created_at) > 90"
        ),
        {"cid": cid},
    )
    older_than_90_days = r90.scalar() or 0

    r180 = await db.execute(
        text(
            "SELECT COUNT(*) FROM candidates "
            "WHERE company_id = :cid "
            "AND julianday('now') - julianday(created_at) > 180"
        ),
        {"cid": cid},
    )
    older_than_180_days = r180.scalar() or 0

    r365 = await db.execute(
        text(
            "SELECT COUNT(*) FROM candidates "
            "WHERE company_id = :cid "
            "AND julianday('now') - julianday(created_at) > 365"
        ),
        {"cid": cid},
    )
    older_than_365_days = r365.scalar() or 0

    # Policy recommendation based on oldest cohort size
    if older_than_365_days > 50:
        policy_recommendation = (
            "⚠️ High volume of records older than 365 days detected. "
            "Immediate data purge recommended per GDPR Article 17 retention limits."
        )
    elif older_than_180_days > 20:
        policy_recommendation = (
            "Review records older than 180 days. "
            "Consider anonymisation or deletion to comply with data minimisation principles."
        )
    elif older_than_90_days > 0:
        policy_recommendation = (
            "Some records exceed 90-day retention. "
            "Schedule a quarterly data audit."
        )
    else:
        policy_recommendation = (
            "✅ All candidate data is within recommended retention windows. No action required."
        )

    return {
        "total_candidates": total_candidates,
        "older_than_90_days": older_than_90_days,
        "older_than_180_days": older_than_180_days,
        "older_than_365_days": older_than_365_days,
        "policy_recommendation": policy_recommendation,
    }


@router.get("/audit-log")
async def get_audit_log(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the 50 most recently updated application events for the
    current user's company, for compliance audit trail purposes.
    """
    cid = str(current_user.company_id)

    result = await db.execute(
        text(
            "SELECT applications.candidate_id, applications.status, applications.updated_at "
            "FROM applications "
            "JOIN jobs ON applications.job_id = jobs.id "
            "WHERE jobs.company_id = :cid "
            "ORDER BY applications.updated_at DESC "
            "LIMIT 50"
        ),
        {"cid": cid},
    )

    rows = result.fetchall()
    return [
        {
            "candidate_id": str(row[0]),
            "action": row[1],
            "timestamp": row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
        }
        for row in rows
    ]
