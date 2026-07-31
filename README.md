# AI Resume Screening & Candidate Ranking SaaS

A commercial-grade, production-ready AI Hiring Copilot built for Small & Medium Businesses (SMBs) and Enterprises.

## 🌟 Architecture Overview

The system follows **Clean Architecture**, **Layered Architecture**, and **SOLID Principles**:

```
backend/
├── app/
│   ├── api/             # API Endpoints (v1, routers)
│   ├── core/            # App Configuration, Database, Logging, Security, Exceptions
│   ├── models/          # SQLAlchemy Base Models & Entities
│   ├── schemas/         # Pydantic Schemas & DTOs
│   ├── services/        # Business Logic & AI Services
│   ├── repositories/    # Data Access Layer (Repository Pattern)
│   └── main.py          # FastAPI Application Factory
├── alembic/             # Database Migration Scripts
├── tests/               # Unit and Integration Tests
├── Dockerfile           # Backend Containerization
└── requirements.txt     # Python Dependencies
```

---

## 🚀 Module 1 Setup & Local Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Virtual environment tool (`venv` or `uv`)

### 1. Environment Configuration

Copy the example environment file:
```bash
cp backend/.env.example backend/.env
```

### 2. Local Python Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Alembic Migrations

```bash
alembic upgrade head
```

### 4. Start Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access API Documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Endpoint**: `http://localhost:8000/api/v1/health`

---

## 🐳 Docker Setup

Run the full stack (FastAPI + PostgreSQL + Redis) using Docker Compose:

```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

Check logs:
```bash
docker-compose -f docker/docker-compose.yml logs -f app
```

---

## 🧪 Testing & Verification

Run automated test suite:

```bash
pytest backend/tests -v
```

---

## ✅ Verification Checklist (Module 1)

- [x] Folder structure following Clean Architecture
- [x] FastAPI application initialization with OpenAPI docs
- [x] Configuration management via Pydantic Settings
- [x] Asynchronous SQLAlchemy 2.0 setup (SQLite & PostgreSQL support)
- [x] Base declarative models with UUID and Timestamp mixins
- [x] Alembic migration framework initialized
- [x] Custom exceptions and global error handling middleware
- [x] Structured JSON logging
- [x] Detailed health check API (System, DB, Redis status)
- [x] Dockerfile & Multi-container Docker Compose setup
- [x] Automated test suite for health check endpoint
# ai-resume-screener
