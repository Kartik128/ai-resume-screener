import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_resume_upload_and_parsing(async_client: AsyncClient):
    # 1. Register and Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "TalentCorp",
            "company_slug": "talentcorp",
            "full_name": "Recruiter Bob",
            "email": "bob@talentcorp.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@talentcorp.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload sample TXT resume
    resume_content = b"""
    John Doe
    Email: john.doe@example.com
    Phone: (555) 019-2831
    Location: New York, NY
    LinkedIn: linkedin.com/in/johndoe

    SUMMARY
    Senior Software Engineer with 6 years of experience in Python, FastAPI, React, and SQL databases.

    WORK EXPERIENCE
    Lead Developer - Acme Solutions (2020 - Present)
    - Architected microservices with FastAPI and PostgreSQL.
    - Managed cloud deployments on AWS Docker instances.

    EDUCATION
    BS Computer Science - NYU (2016 - 2020)
    """

    files = {"file": ("sample_resume.txt", io.BytesIO(resume_content), "text/plain")}
    upload_resp = await async_client.post("/api/v1/resumes/upload", headers=headers, files=files)
    assert upload_resp.status_code == 201
    resume_data = upload_resp.json()
    assert resume_data["parsing_status"] == "parsed"
    candidate_id = resume_data["candidate_id"]

    # 3. Fetch Candidate Profile
    cand_resp = await async_client.get(f"/api/v1/resumes/candidate/{candidate_id}", headers=headers)
    assert cand_resp.status_code == 200
    candidate_data = cand_resp.json()
    assert candidate_data["full_name"] is not None
    assert len(candidate_data["resumes"]) == 1
