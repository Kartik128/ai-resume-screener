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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan events for application startup and shutdown."""
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    async with engine.begin() as conn:
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
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
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
        }    "health": f"{settings.API_V1_STR}/health",
        }
