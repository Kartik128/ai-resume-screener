from fastapi import APIRouter
from app.api.v1.endpoints import (
    analytics,
    auth,
    copilot,
    dashboard,
    exports,
    governance,
    health,
    intelligence,
    jobs,
    pipeline,
    rediscover,
    resumes,
    scorecards,
    score_overrides,
    scoring,
    summary,
    users,
    assessments,
    webhooks,
    transcripts,
    intake,
    experience,
    offers,
    quality_of_hire,
    workforce_planning,
    campaigns,
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
api_router.include_router(scorecards.router, prefix="/scorecards", tags=["Recruiter Scorecards & Custom Weights"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["Hiring Pipeline & Activity Audit Log"])
api_router.include_router(score_overrides.router, prefix="/scores", tags=["Recruiter Score Overrides & Manual Calibration"])
api_router.include_router(rediscover.router, prefix="/rediscover", tags=["Talent Rediscovery & Past Applicant Search"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["Lightweight Skill Validation Assessments"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Integration Hub Webhooks Platform"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["Interview Intelligence Audio Transcription"])
api_router.include_router(intake.router, prefix="/intake", tags=["Hiring Manager Intake Copilot Platform"])
api_router.include_router(experience.router, prefix="/experience", tags=["Candidate Portal Experience NPS Feedback"])
api_router.include_router(offers.router, prefix="/offers", tags=["Offer Letters Release & Sign Workflow"])
api_router.include_router(quality_of_hire.router, prefix="/quality-of-hire", tags=["Quality-of-Hire Post-Hire Review Engine"])
api_router.include_router(workforce_planning.router, prefix="/workforce", tags=["Workforce Planning & Headcount Forecast"])
api_router.include_router(governance.router, prefix="/governance", tags=["Governance & GDPR Compliance"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Automated Outreach Campaigns Drip sequences"])

