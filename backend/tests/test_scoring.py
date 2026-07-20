import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_candidate_scoring_and_leaderboard(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Scoring Inc",
            "company_slug": "scoring-inc",
            "full_name": "Lead Recruiter",
            "email": "lead@scoring.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "lead@scoring.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Job Posting
    job_payload = {
        "title": "Senior Data Analyst",
        "department": "Analytics",
        "raw_description": "We need a Senior Data Analyst with 4+ years experience in Power BI, SQL, and Python.",
        "status": "active",
        "min_experience_years": 4.0,
        "location": "San Francisco, CA",
        "is_remote": True,
        "mandatory_skills": [{"name": "Power BI"}, {"name": "SQL"}],
        "good_to_have_skills": [{"name": "Python"}],
    }
    job_resp = await async_client.post("/api/v1/jobs/", headers=headers, json=job_payload)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # 3. Upload Candidate Resume
    resume_text = b"""
    Alice Smith
    Email: alice.smith@example.com
    Location: San Francisco, CA
    SUMMARY: 5 years of analytics experience with Power BI, DAX, SQL, and Python.
    WORK EXPERIENCE: Senior Analyst - TechCorp (2020 - Present)
    EDUCATION: BS Statistics - Berkeley (2019)
    """
    files = {"file": ("alice_resume.txt", io.BytesIO(resume_text), "text/plain")}
    data = {"job_id": job_id}
    upload_resp = await async_client.post(
        "/api/v1/resumes/upload", headers=headers, files=files, data=data
    )
    assert upload_resp.status_code == 201
    cand_id = upload_resp.json()["candidate_id"]

    # 4. Evaluate Candidate Score
    eval_resp = await async_client.post(
        f"/api/v1/scoring/evaluate/{job_id}/{cand_id}", headers=headers
    )
    assert eval_resp.status_code == 200
    score_data = eval_resp.json()
    assert score_data["overall_score"] >= 80.0
    assert "mandatory_skills" in score_data
    assert score_data["mandatory_skills"]["weight_percentage"] == 35.0

    # 5. Fetch Leaderboard
    leader_resp = await async_client.get(
        f"/api/v1/scoring/leaderboard/{job_id}", headers=headers
    )
    assert leader_resp.status_code == 200
    assert len(leader_resp.json()) == 1
    assert leader_resp.json()[0]["candidate_id"] == cand_id
