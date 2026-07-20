import time
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthCheckResponse, ServiceStatus

router = APIRouter()
START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed System Health Check",
    description="Check the operational status of the application, database, and Redis cache.",
)
async def get_health_status(
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    services = {}
    overall_healthy = True

    # 1. Database Check
    db_start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - db_start) * 1000
        services["database"] = ServiceStatus(
            status="online",
            latency_ms=round(db_latency, 2),
        )
    except Exception as e:
        overall_healthy = False
        services["database"] = ServiceStatus(
            status="offline",
            error=str(e),
        )

    # 2. Redis Check
    redis_start = time.perf_counter()
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        await redis_client.ping()
        await redis_client.close()
        redis_latency = (time.perf_counter() - redis_start) * 1000
        services["redis"] = ServiceStatus(
            status="online",
            latency_ms=round(redis_latency, 2),
        )
    except Exception as e:
        # Mark degraded rather than failing health check completely if Redis is optional in early startup
        services["redis"] = ServiceStatus(
            status="degraded",
            error=str(e),
        )

    uptime = round(time.time() - START_TIME, 2)

    return HealthCheckResponse(
        status="healthy" if overall_healthy else "unhealthy",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        uptime_seconds=uptime,
        services=services,
    )
