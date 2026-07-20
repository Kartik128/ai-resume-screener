import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_interview_questions_and_red_flag_detection(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Copilot HR",
            "company_slug": "copilot-hr",
            "full_name": "Auditor Tom",
            "email": "tom@copilothr.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "tom@copilothr.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Job Posting
    job_payload = {
        "title": "Lead DevOps Architect",
        "department": "Infrastructure",
        "raw_description": "Architect needed with 8+ years experience in Kubernetes, Terraform, Docker, AWS.",
        "status": "active",
        "min_experience_years": 8.0,
    }
    job_resp = await async_client.post("/api/v1/jobs/", headers=headers, json=job_payload)
    job_id = job_resp.json()["id"]

    # 3. Upload Resume with 2 yrs exp (trigger underqualified red flag)
    resume_text = b"""
    Charlie Brown
    Email: charlie@example.com
    SUMMARY: Junior DevOps engineer with 2 years experience in Docker and AWS.
    WORK HISTORY: Junior Admin - SmallCo (2022 - 2024)
    """
    files = {"file": ("charlie_resume.txt", io.BytesIO(resume_text), "text/plain")}
    data = {"job_id": job_id}
    upload_resp = await async_client.post(
        "/api/v1/resumes/upload", headers=headers, files=files, data=data
    )
    cand_id = upload_resp.json()["candidate_id"]

    # 4. Test Interview Question Generation
    q_resp = await async_client.get(
        f"/api/v1/copilot/interview-questions/{job_id}/{cand_id}", headers=headers
    )
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert "questions" in q_data
    assert len(q_data["questions"]) >= 3

    # 5. Test Red Flag Anomaly Detection
    flag_resp = await async_client.get(
        f"/api/v1/copilot/red-flags/{job_id}/{cand_id}", headers=headers
    )
    assert flag_resp.status_code == 200
    flag_data = flag_resp.json()
    assert "red_flags" in flag_data
    assert flag_data["risk_score"] > 0.0
