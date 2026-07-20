from typing import Dict, Optional
from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    status: str = Field(..., description="Status of the service ('online', 'offline', 'degraded')")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    error: Optional[str] = Field(None, description="Error message if offline/degraded")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall application status ('healthy', 'unhealthy')")
    environment: str = Field(..., description="Runtime environment")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    services: Dict[str, ServiceStatus] = Field(..., description="Status of downstream services")
