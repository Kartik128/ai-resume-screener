from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import HRAnalyticsDashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get(
    "/overview",
    response_model=HRAnalyticsDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tenant-wide HR analytics, hiring funnel conversion, top skills & skill gap metrics",
)
async def get_hr_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HRAnalyticsDashboardResponse:
    return await AnalyticsService.get_tenant_analytics(current_user.company_id, db)
