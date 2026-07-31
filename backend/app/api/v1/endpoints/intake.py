"""
Hiring Manager Intake Copilot endpoints — process intake discussion notes and output scorecard recommendations.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class IntakeNotesRequest(BaseModel):
    notes: str = Field(..., min_length=1, max_length=5000, description="Intake conversation script or bulleted requirements")


class IntakeAnalysisResponse(BaseModel):
    summary: str
    suggested_skills: list[str]
    suggested_weights: dict[str, int]
    suggested_scorecard_rules: list[str]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=IntakeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Process intake notes to output scorecard recommendations and calibration rules",
)
async def process_intake_notes(
    body: IntakeNotesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Standard NLP parsing simulations matching recruiter interest
    notes_lower = body.notes.lower()

    # Dynamic suggestions mapping
    skills = ["Python", "SQL", "Docker"]
    weights = {"experience_weight": 40, "skills_weight": 35, "education_weight": 25}
    rules = [
        "Candidates should have worked with containerization toolsets.",
        "Look for clean coding guidelines matching test suite preferences."
    ]

    if "lead" in notes_lower or "senior" in notes_lower:
        weights = {"experience_weight": 60, "skills_weight": 25, "education_weight": 15}
        skills.extend(["System Architecture", "Team Leadership"])
        rules.append("Prior experience managing teams or scoping architectural plans is highly valued.")
    elif "frontend" in notes_lower or "react" in notes_lower:
        skills.extend(["React", "TypeScript", "TailwindCSS"])
        weights = {"experience_weight": 30, "skills_weight": 50, "education_weight": 20}
        rules.append("Verify active portfolio assets or complex state management frameworks.")

    summary = (
        f"Intake transcript processed successfully. The role profile emphasizes technical capabilities. "
        f"Recommended alignment weight allocations: Experience ({weights['experience_weight']}%), "
        f"Skills ({weights['skills_weight']}%), Education ({weights['education_weight']}%)."
    )

    return IntakeAnalysisResponse(
        summary=summary,
        suggested_skills=skills,
        suggested_weights=weights,
        suggested_scorecard_rules=rules
    )
