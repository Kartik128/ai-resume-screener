"""
Scoring overrides endpoints — allow recruiters to manually override specific component scores,
auto-recalculating overall scores and maintaining a detailed audit log.
"""
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.score import Score
from app.models.score_override import ScoreOverride
from app.schemas.scoring import ScoreBreakdownResponse

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class ScoreOverrideRequest(BaseModel):
    dimension: str = Field(..., description="The score category to override (e.g., 'mandatory_skills')")
    new_raw_score: float = Field(..., ge=0.0, le=100.0, description="The override raw score (0-100)")
    reason: str = Field(..., min_length=5, max_length=2000, description="Explanation for manual adjustment")


class ScoreOverrideAuditOut(BaseModel):
    id: uuid.UUID
    dimension: str
    original_value: float
    new_value: float
    reason: str
    overridden_by_name: str
    created_at: datetime


# ── Helper: Re-compute Overall Score ─────────────────────────────────────────

def _recompute_overall(breakdown_dict: dict) -> float:
    """Sum all dimensions' weighted scores to calculate new overall score."""
    overall = 0.0
    keys = [
        "mandatory_skills", "experience", "nice_to_have_skills", 
        "career_stability", "industry_match", "education", 
        "certifications", "location"
    ]
    for k in keys:
        if k in breakdown_dict:
            overall += breakdown_dict[k].get("weighted_score", 0.0)
    return round(min(overall, 100.0), 1)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{score_id}/override",
    status_code=status.HTTP_200_OK,
    summary="Override a dimension score (e.g. mandatory_skills) and recalculate candidate ranking score",
)
async def override_score(
    score_id: uuid.UUID,
    body: ScoreOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch original score entity
    result = await db.execute(select(Score).where(Score.id == score_id))
    score_ent = result.scalar_one_or_none()
    if not score_ent:
        raise NotFoundException(resource="Score record", identifier=score_id)

    bd = dict(score_ent.match_breakdown or {})
    if body.dimension not in bd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dimension '{body.dimension}' is not a valid score dimension. Choose from: {list(bd.keys())}"
        )

    orig_comp = bd[body.dimension]
    orig_raw = orig_comp.get("raw_score", 0.0)
    weight_pct = orig_comp.get("weight_percentage", 0.0)

    # Calculate new weighted score
    new_weighted = round((body.new_raw_score * weight_pct) / 100.0, 2)

    # Apply override locally in JSON
    bd[body.dimension]["raw_score"] = body.new_raw_score
    bd[body.dimension]["weighted_score"] = new_weighted
    bd[body.dimension]["reasoning"] = f"[Manual Override by {current_user.full_name or current_user.email}]: {body.reason} (Original score: {orig_raw:.0f}/100)"

    # Recalculate overall score
    new_overall = _recompute_overall(bd)

    # Save to Score entity
    score_ent.match_breakdown = bd
    score_ent.overall_score = new_overall
    if body.dimension == "mandatory_skills":
        score_ent.mandatory_skills_score = body.new_raw_score
    elif body.dimension == "experience":
        score_ent.experience_score = body.new_raw_score

    # Save override history audit log
    history = ScoreOverride(
        score_id=score_id,
        dimension=body.dimension,
        original_value=orig_raw,
        new_value=body.new_raw_score,
        overridden_by=current_user.id,
        reason=body.reason
    )
    db.add(history)
    await db.commit()

    return {
        "success": True,
        "score_id": str(score_id),
        "new_overall_score": new_overall,
        "dimension": body.dimension,
        "new_raw_score": body.new_raw_score
    }


@router.get(
    "/{score_id}/audit",
    response_model=List[ScoreOverrideAuditOut],
    status_code=status.HTTP_200_OK,
    summary="Get manual score override audit trail for a candidate",
)
async def get_score_audit_trail(
    score_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScoreOverride)
        .where(ScoreOverride.score_id == score_id)
        .order_by(ScoreOverride.created_at.desc())
    )
    overrides = result.scalars().all()

    return [
        ScoreOverrideAuditOut(
            id=o.id,
            dimension=o.dimension,
            original_value=o.original_value,
            new_value=o.new_value,
            reason=o.reason,
            overridden_by_name=(
                o.actor.full_name or o.actor.email if o.actor else "System"
            ),
            created_at=o.created_at
        )
        for o in overrides
    ]
