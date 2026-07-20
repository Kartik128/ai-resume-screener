import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_candidate_summary_and_gap_analysis(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Summary Corp",
            "company_slug": "summary-corp",
            "full_name": "Recruiter Jane",
            "email": "jane@summarycorp.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "jane@summarycorp.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Job Posting
    job_payload = {
        "title": "HR Analytics Specialist",
        "department": "HR",
        "raw_description": "Looking for HR Analytics Specialist with 6+ years experience in Power BI, SQL, Compensation. Python required.",
        "status": "active",
        "min_experience_years": 6.0,
        "location": "New York, NY",
        "is_remote": False,
        "mandatory_skills": [{"name": "Power BI"}, {"name": "SQL"}, {"name": "Python"}],
    }
    job_resp = await async_client.post("/api/v1/jobs/", headers=headers, json=job_payload)
    job_id = job_resp.json()["id"]

    # 3. Upload Resume (Missing Python, 4 yrs exp vs 6 yrs required, Location mismatch)
    resume_text = b"""
    Bob Miller
    Email: bob.m@example.com
    Location: Austin, TX
    SUMMARY: 4 years of experience in HR Analytics, Power BI, SQL, and Compensation.
    EXPERIENCE: HR Analyst - People Solutions (2020 - Present)
    """
    files = {"file": ("bob_resume.txt", io.BytesIO(resume_text), "text/plain")}
    data = {"job_id": job_id}
    upload_resp = await async_client.post(
        "/api/v1/resumes/upload", headers=headers, files=files, data=data
    )
    cand_id = upload_resp.json()["candidate_id"]

    # 4. Fetch Summary & Gap Highlights
    sum_resp = await async_client.get(f"/api/v1/summary/{job_id}/{cand_id}", headers=headers)
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert "executive_summary" in sum_data
    assert "missing_mandatory_skills" in sum_data
    assert "Python" in sum_data["missing_mandatory_skills"]
    assert sum_data["weak_experience_warning"] is not None
    assert sum_data["location_mismatch_warning"] is not None
