"""
Workforce Planning API — headcount forecasting, cost-per-hire tracking, and
actual-vs-plan gap analysis to connect recruitment pipeline to business demand.
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────────────────────

class HeadcountPlanRequest(BaseModel):
    department: str = Field(..., max_length=120)
    role_title: str = Field(..., max_length=200)
    planned_count: int = Field(1, ge=1, le=500)
    target_quarter: str = Field(..., pattern=r"^Q[1-4]-\d{4}$", description="e.g. Q3-2025")
    estimated_cost_usd: Optional[int] = Field(None, ge=0, description="All-in estimated cost per head in USD")
    status: Optional[str] = Field("open", pattern="^(open|on_track|at_risk|closed)$")


class HeadcountPlanOut(BaseModel):
    id: uuid.UUID
    department: str
    role_title: str
    planned_count: int
    actual_hired: int
    target_quarter: str
    estimated_cost_usd: int
    status: str
    fill_rate: float          # actual_hired / planned_count %
    budget_utilised_usd: int  # actual_hired * estimated_cost_usd


class WorkforceSummary(BaseModel):
    total_planned: int
    total_hired: int
    overall_fill_rate: float
    total_budget_usd: int
    total_budget_utilised_usd: int
    by_department: List[dict]
    plans: List[HeadcountPlanOut]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/plans",
    response_model=HeadcountPlanOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a headcount demand plan for a role in a given quarter",
)
async def create_plan(
    body: HeadcountPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_id = uuid.uuid4()
    cost = body.estimated_cost_usd or 0
    await db.execute(
        text("""
            INSERT INTO headcount_plans (id, company_id, department, role_title, planned_count,
              actual_hired, target_quarter, estimated_cost_usd, status)
            VALUES (:id, :cid, :dept, :role, :planned, 0, :quarter, :cost, :status)
        """),
        {
            "id": str(plan_id), "cid": str(current_user.company_id),
            "dept": body.department, "role": body.role_title,
            "planned": body.planned_count, "quarter": body.target_quarter,
            "cost": cost, "status": body.status,
        }
    )
    await db.commit()
    return HeadcountPlanOut(
        id=plan_id, department=body.department, role_title=body.role_title,
        planned_count=body.planned_count, actual_hired=0, target_quarter=body.target_quarter,
        estimated_cost_usd=cost, status=body.status or "open",
        fill_rate=0.0, budget_utilised_usd=0,
    )


@router.get(
    "/summary",
    response_model=WorkforceSummary,
    summary="Get workforce planning summary with department-level fill rates and budget utilisation",
)
async def workforce_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        text("SELECT * FROM headcount_plans WHERE company_id = :cid ORDER BY target_quarter, department"),
        {"cid": str(current_user.company_id)}
    )
    rows = res.mappings().all()

    plans = []
    dept_map: dict = {}
    total_planned = 0
    total_hired = 0
    total_budget = 0
    total_spent = 0

    for r in rows:
        planned = r["planned_count"]
        hired = r["actual_hired"]
        cost = r["estimated_cost_usd"] or 0
        fill_rate = round((hired / planned * 100), 1) if planned else 0
        spent = hired * cost

        total_planned += planned
        total_hired += hired
        total_budget += planned * cost
        total_spent += spent

        dept = r["department"]
        if dept not in dept_map:
            dept_map[dept] = {"department": dept, "planned": 0, "hired": 0, "budget": 0}
        dept_map[dept]["planned"] += planned
        dept_map[dept]["hired"] += hired
        dept_map[dept]["budget"] += planned * cost

        plans.append(HeadcountPlanOut(
            id=uuid.UUID(r["id"]), department=dept, role_title=r["role_title"],
            planned_count=planned, actual_hired=hired, target_quarter=r["target_quarter"],
            estimated_cost_usd=cost, status=r["status"],
            fill_rate=fill_rate, budget_utilised_usd=spent,
        ))

    by_dept = []
    for d in dept_map.values():
        p, h = d["planned"], d["hired"]
        by_dept.append({
            "department": d["department"],
            "planned": p,
            "hired": h,
            "fill_rate": round(h / p * 100, 1) if p else 0,
            "budget_usd": d["budget"],
        })

    overall_fill = round(total_hired / total_planned * 100, 1) if total_planned else 0

    return WorkforceSummary(
        total_planned=total_planned,
        total_hired=total_hired,
        overall_fill_rate=overall_fill,
        total_budget_usd=total_budget,
        total_budget_utilised_usd=total_spent,
        by_department=sorted(by_dept, key=lambda x: x["fill_rate"]),
        plans=plans,
    )


@router.patch(
    "/plans/{plan_id}/increment",
    response_model=HeadcountPlanOut,
    summary="Increment actual_hired count when a candidate is marked 'joined' for this plan's role",
)
async def increment_hired(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        text("SELECT * FROM headcount_plans WHERE id = :id AND company_id = :cid"),
        {"id": str(plan_id), "cid": str(current_user.company_id)}
    )
    row = res.mappings().first()
    if not row:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(resource="Headcount Plan", identifier=plan_id)

    new_hired = row["actual_hired"] + 1
    new_status = "closed" if new_hired >= row["planned_count"] else "on_track"
    await db.execute(
        text("UPDATE headcount_plans SET actual_hired = :h, status = :s WHERE id = :id"),
        {"h": new_hired, "s": new_status, "id": str(plan_id)}
    )
    await db.commit()

    cost = row["estimated_cost_usd"] or 0
    fill_rate = round(new_hired / row["planned_count"] * 100, 1)
    return HeadcountPlanOut(
        id=plan_id, department=row["department"], role_title=row["role_title"],
        planned_count=row["planned_count"], actual_hired=new_hired,
        target_quarter=row["target_quarter"], estimated_cost_usd=cost,
        status=new_status, fill_rate=fill_rate, budget_utilised_usd=new_hired * cost,
    )
