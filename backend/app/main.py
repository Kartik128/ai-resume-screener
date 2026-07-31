from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from sqlalchemy import select
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.models.base import Base
from app.core.database import async_engine as engine, AsyncSessionLocal

# Ensure all ORM models are registered with Base
import app.models  # noqa: F401


from app.models.company import Company
from app.models.user import User, UserRole
from app.core.security import get_password_hash


from sqlalchemy import select, text

# ...

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan events for application startup and shutdown."""
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    async with engine.begin() as conn:
        if "sqlite" in settings.DATABASE_URL:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA busy_timeout=30000;"))
        await conn.run_sync(Base.metadata.create_all)

    # Seed Default Admin Credentials (admin@company.com / admin)
    async with AsyncSessionLocal() as db:
        try:
            user_exists = await db.execute(select(User).where(User.email == "admin@company.com"))
            if not user_exists.scalar_one_or_none():
                company = Company(name="Demo Company", slug="demo-company")
                db.add(company)
                await db.flush()

                admin_user = User(
                    email="admin@company.com",
                    hashed_password=get_password_hash("admin"),
                    full_name="Admin User",
                    company_id=company.id,
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                db.add(admin_user)
                await db.commit()
                logger.info("Successfully seeded default admin user: admin@company.com / admin")
        except Exception as e:
            logger.warning(f"Seeding skipped or already initialized: {e}")

    # Seed default Jobs and Candidates if database is empty
    async with AsyncSessionLocal() as db:
        try:
            from app.models.job import Job, JobStatus
            from app.models.candidate import Candidate
            from app.models.resume import Resume, ParsingStatus
            from app.models.application import Application, ApplicationStatus
            from app.services.scoring_engine_service import ScoringEngineService
            from app.repositories.score_repository import ScoreRepository

            # Check if any jobs exist
            jobs_count = await db.execute(select(Job))
            if not jobs_count.scalars().first():
                # Get the demo company and user
                comp_res = await db.execute(select(Company).where(Company.slug == "demo-company"))
                company = comp_res.scalar_one()

                user_res = await db.execute(select(User).where(User.email == "admin@company.com"))
                admin_user = user_res.scalar_one()

                # 1. Create Job: Senior Cloud Architect
                job_1 = Job(
                    company_id=company.id,
                    creator_id=admin_user.id,
                    title="Senior Cloud Architect",
                    department="Engineering",
                    raw_description="We are seeking a Senior Cloud Architect to lead our cloud infrastructure scaling efforts. Required skills include AWS, Docker, Kubernetes, and Terraform. Minimum 5 years of experience.",
                    status=JobStatus.ACTIVE,
                    min_experience_years=5.0,
                    max_experience_years=15.0,
                    location="San Francisco, CA",
                    is_remote=True,
                    responsibilities=["Design highly-scalable cloud architectures", "Maintain CI/CD pipelines", "Implement distributed databases"],
                    parsed_data={
                        "mandatory_skills": [
                            {"name": "AWS", "weight": 40},
                            {"name": "Docker", "weight": 20},
                            {"name": "Kubernetes", "weight": 20},
                            {"name": "Terraform", "weight": 20}
                        ],
                        "nice_to_have_skills": [
                            {"name": "Go", "weight": 50},
                            {"name": "GraphQL", "weight": 50}
                        ],
                        "experience": {"min_years": 5.0}
                    }
                )
                db.add(job_1)

                # 2. Create Job: Lead Frontend Engineer
                job_2 = Job(
                    company_id=company.id,
                    creator_id=admin_user.id,
                    title="Lead Frontend Engineer",
                    department="Engineering",
                    raw_description="Looking for a Lead Frontend Engineer with strong React, TypeScript, and TailwindCSS skills. Minimum 4 years of experience.",
                    status=JobStatus.ACTIVE,
                    min_experience_years=4.0,
                    max_experience_years=12.0,
                    location="New York, NY",
                    is_remote=False,
                    responsibilities=["Build premium web applications", "Optimize frontend load speeds", "Manage engineering tasks"],
                    parsed_data={
                        "mandatory_skills": [
                            {"name": "React", "weight": 40},
                            {"name": "TypeScript", "weight": 30},
                            {"name": "TailwindCSS", "weight": 15},
                            {"name": "Next.js", "weight": 15}
                        ],
                        "nice_to_have_skills": [],
                        "experience": {"min_years": 4.0}
                    }
                )
                db.add(job_2)
                await db.flush()

                # 3. Create Candidates
                # Cand 1 for Job 2
                cand_1 = Candidate(
                    company_id=company.id,
                    full_name="Sarah Jenkins",
                    email="sarah.j@example.com",
                    phone="+1 555-0192",
                    location="New York, NY",
                    total_experience_years=6.0,
                    raw_skills=["React", "TypeScript", "TailwindCSS", "Next.js", "CSS", "HTML", "Javascript"],
                    summary="Senior Frontend Developer specializing in React and modern CSS systems."
                )
                db.add(cand_1)

                # Cand 2 for Job 1
                cand_2 = Candidate(
                    company_id=company.id,
                    full_name="Michael Chen",
                    email="m.chen@example.com",
                    phone="+1 555-0188",
                    location="San Francisco, CA",
                    total_experience_years=7.5,
                    raw_skills=["AWS", "Docker", "Kubernetes", "Terraform", "Go", "Python", "Linux"],
                    summary="DevOps Engineer focused on Infrastructure as Code and cloud systems orchestration."
                )
                db.add(cand_2)

                # Cand 3 for Job 2
                cand_3 = Candidate(
                    company_id=company.id,
                    full_name="Emma Watson",
                    email="emma.w@example.com",
                    phone="+1 555-0123",
                    location="London, UK",
                    total_experience_years=2.0,
                    raw_skills=["Python", "Javascript", "CSS", "HTML"],
                    summary="Junior developer looking to grow tech capabilities in React/Node ecosystem."
                )
                db.add(cand_3)
                await db.flush()

                # 4. Create Resumes
                r1 = Resume(
                    candidate_id=cand_1.id,
                    job_id=job_2.id,
                    file_name="sarah_jenkins_resume.pdf",
                    file_path="uploads/sarah_jenkins_resume.pdf",
                    file_type="pdf",
                    file_size_bytes=24500,
                    parsing_status=ParsingStatus.PARSED,
                    raw_text="Sarah Jenkins. 6 years React, TypeScript, Next.js, and TailwindCSS experience. Built responsive SaaS dashboards.",
                    parsed_data={"skills": [{"name": "React"}, {"name": "TypeScript"}, {"name": "TailwindCSS"}, {"name": "Next.js"}]}
                )
                db.add(r1)

                r2 = Resume(
                    candidate_id=cand_2.id,
                    job_id=job_1.id,
                    file_name="michael_chen_resume.pdf",
                    file_path="uploads/michael_chen_resume.pdf",
                    file_type="pdf",
                    file_size_bytes=31200,
                    parsing_status=ParsingStatus.PARSED,
                    raw_text="Michael Chen. DevOps engineer with 7.5 years experience scaling clouds on AWS, writing Terraform scripts, and containerizing with Docker/Kubernetes.",
                    parsed_data={"skills": [{"name": "AWS"}, {"name": "Docker"}, {"name": "Kubernetes"}, {"name": "Terraform"}]}
                )
                db.add(r2)

                r3 = Resume(
                    candidate_id=cand_3.id,
                    job_id=job_2.id,
                    file_name="emma_watson_resume.pdf",
                    file_path="uploads/emma_watson_resume.pdf",
                    file_type="pdf",
                    file_size_bytes=19800,
                    parsing_status=ParsingStatus.PARSED,
                    raw_text="Emma Watson. Junior software engineer. Experienced in basic Python scripting, HTML/CSS layout creation, and Javascript animations.",
                    parsed_data={"skills": [{"name": "Python"}, {"name": "Javascript"}, {"name": "HTML"}, {"name": "CSS"}]}
                )
                db.add(r3)
                await db.flush()

                # 5. Create Applications
                app_1 = Application(
                    job_id=job_2.id,
                    candidate_id=cand_1.id,
                    recruiter_id=admin_user.id,
                    status=ApplicationStatus.SHORTLISTED
                )
                db.add(app_1)

                app_2 = Application(
                    job_id=job_1.id,
                    candidate_id=cand_2.id,
                    recruiter_id=admin_user.id,
                    status=ApplicationStatus.APPLIED
                )
                db.add(app_2)

                app_3 = Application(
                    job_id=job_2.id,
                    candidate_id=cand_3.id,
                    recruiter_id=admin_user.id,
                    status=ApplicationStatus.REJECTED
                )
                db.add(app_3)
                await db.flush()

                # 6. Pre-calculate Scores (Offline seeding to prevent OpenAI credit/API failure blockers)
                from app.models.score import Score
                
                s1 = Score(
                    job_id=job_2.id,
                    candidate_id=cand_1.id,
                    resume_id=r1.id,
                    overall_score=92.5,
                    mandatory_skills_score=100.0,
                    nice_skills_score=0.0,
                    experience_score=95.0,
                    education_score=90.0,
                    industry_score=90.0,
                    location_score=100.0,
                    stability_score=90.0,
                    certification_score=0.0,
                    semantic_similarity=1.0,
                    match_breakdown={
                        "overall_score": 92.5,
                        "match_summary": "Excellent frontend developer. Matches React, TypeScript, and Next.js requirements perfectly.",
                        "mandatory_skills": {"raw_score": 100.0, "reasoning": "React, TypeScript, TailwindCSS, Next.js present.", "citations": []},
                        "nice_to_have_skills": {"raw_score": 0.0, "reasoning": "No nice-to-have skills required.", "citations": []},
                        "experience": {"raw_score": 95.0, "reasoning": "6.0 years experience exceeds the 4-year requirement.", "citations": []},
                        "education": {"raw_score": 90.0, "reasoning": "Relevant software background.", "citations": []},
                        "location": {"raw_score": 100.0, "reasoning": "Based in New York, NY (Office match).", "citations": []},
                        "career_stability": {"raw_score": 90.0, "reasoning": "Good tenure history.", "citations": []},
                        "industry_match": {"raw_score": 90.0, "reasoning": "Strong product development background.", "citations": []},
                        "certifications": {"raw_score": 0.0, "reasoning": "", "citations": []}
                    }
                )
                db.add(s1)

                s2 = Score(
                    job_id=job_1.id,
                    candidate_id=cand_2.id,
                    resume_id=r2.id,
                    overall_score=89.0,
                    mandatory_skills_score=95.0,
                    nice_skills_score=50.0,
                    experience_score=92.0,
                    education_score=85.0,
                    industry_score=90.0,
                    location_score=100.0,
                    stability_score=85.0,
                    certification_score=0.0,
                    semantic_similarity=0.95,
                    match_breakdown={
                        "overall_score": 89.0,
                        "match_summary": "Strong Cloud Architect. Demonstrates deep AWS, Docker, Kubernetes, and Terraform expertise.",
                        "mandatory_skills": {"raw_score": 95.0, "reasoning": "AWS, Docker, Kubernetes, Terraform present.", "citations": []},
                        "nice_to_have_skills": {"raw_score": 50.0, "reasoning": "Go present, missing GraphQL.", "citations": []},
                        "experience": {"raw_score": 92.0, "reasoning": "7.5 years experience fits the 5-year target.", "citations": []},
                        "education": {"raw_score": 85.0, "reasoning": "Technical background.", "citations": []},
                        "location": {"raw_score": 100.0, "reasoning": "San Francisco base matches job posting details.", "citations": []},
                        "career_stability": {"raw_score": 85.0, "reasoning": "Average tenure of 2.5 years per role.", "citations": []},
                        "industry_match": {"raw_score": 90.0, "reasoning": "Infrastructure cloud architect focus.", "citations": []},
                        "certifications": {"raw_score": 0.0, "reasoning": "", "citations": []}
                    }
                )
                db.add(s2)

                s3 = Score(
                    job_id=job_2.id,
                    candidate_id=cand_3.id,
                    resume_id=r3.id,
                    overall_score=45.0,
                    mandatory_skills_score=35.0,
                    nice_skills_score=0.0,
                    experience_score=40.0,
                    education_score=80.0,
                    industry_score=50.0,
                    location_score=0.0,
                    stability_score=90.0,
                    certification_score=0.0,
                    semantic_similarity=0.35,
                    match_breakdown={
                        "overall_score": 45.0,
                        "match_summary": "Underqualified developer. Missing React, TypeScript, and TailwindCSS framework skills.",
                        "mandatory_skills": {"raw_score": 35.0, "reasoning": "Only general Javascript present. Missing React and TypeScript.", "citations": []},
                        "nice_to_have_skills": {"raw_score": 0.0, "reasoning": "", "citations": []},
                        "experience": {"raw_score": 40.0, "reasoning": "2.0 years experience is below the 4-year requirement.", "citations": []},
                        "education": {"raw_score": 80.0, "reasoning": "Basic degree.", "citations": []},
                        "location": {"raw_score": 0.0, "reasoning": "Based in London (Job is in NY).", "citations": []},
                        "career_stability": {"raw_score": 90.0, "reasoning": "Stable junior trajectory.", "citations": []},
                        "industry_match": {"raw_score": 50.0, "reasoning": "Limited commercial experience.", "citations": []},
                        "certifications": {"raw_score": 0.0, "reasoning": "", "citations": []}
                    }
                )
                db.add(s3)

                await db.commit()
                logger.info("Successfully seeded default jobs, candidates, and evaluation scores for the live demo!")
        except Exception as e:
            logger.error(f"Failed to seed demo data: {e}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description=(
        "Production-Grade AI Resume Screening & Candidate Ranking SaaS API.\n\n"
        "Features:\n"
        "- Automated Resume Parsing & Structured Extraction\n"
        "- Deep Semantic Job-Resume Matching\n"
        "- Explainable Weighted Candidate Scoring Engine\n"
        "- Recruiter Summary & Custom AI Interview Question Generation\n"
        "- Anomaly & Red Flag Detection\n"
        "- Recruiter Feedback Loop & System Learning"
    ),
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Multi-candidate frontend dist resolution
candidate_paths = [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent.parent / "frontend_dist",
    Path.cwd() / "frontend" / "dist",
    Path.cwd().parent / "frontend" / "dist",
]

frontend_dist = None
for p in candidate_paths:
    if p.exists() and (p / "index.html").exists():
        frontend_dist = p
        break

if frontend_dist:
    logger.info(f"Serving SPA frontend from: {frontend_dist}")
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api" or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("redoc"):
            raise StarletteHTTPException(status_code=404)
        file_path = frontend_dist / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    logger.warning("SPA frontend dist not found. Serving default API root response.")
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health",
        }
