from fastapi import APIRouter
from app.api.v1.endpoints import (
    analytics,
    auth,
    copilot,
    dashboard,
    exports,
    health,
    intelligence,
    jobs,
    resumes,
    scoring,
    summary,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Tenant"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Job Description Module"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resume Upload & Parser Module"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["AI Semantic Intelligence Module"])
api_router.include_router(scoring.router, prefix="/scoring", tags=["Explainable AI Scoring Engine"])
api_router.include_router(summary.router, prefix="/summary", tags=["AI Candidate Summary & Gap Highlights"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["AI Copilot: Interview Questions & Red Flags"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Recruiter Dashboard & Comparison Module"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["HR Analytics & Hiring Funnel Module"])
api_router.include_router(exports.router, prefix="/exports", tags=["CSV, Excel & PDF Export Module"])
