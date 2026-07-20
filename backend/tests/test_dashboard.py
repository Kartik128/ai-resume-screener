import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_candidate_cards_comparison_and_feedback(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Dashboard Tech",
            "company_slug": "dashboard-tech",
            "full_name": "Recruiter Sam",
            "email": "sam@dashboardtech.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "sam@dashboardtech.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Job Posting
    job_payload = {
        "title": "Lead Software Architect",
        "department": "Engineering",
        "raw_description": "Architect needed with Python, FastApi, React.",
        "status": "active",
        "mandatory_skills": [{"name": "Python"}, {"name": "React"}],
    }
    job_resp = await async_client.post("/api/v1/jobs/", headers=headers, json=job_payload)
    job_id = job_resp.json()["id"]

    # 3. Upload 2 Candidates
    r1 = b"Candidate One\nEmail: c1@test.com\nPython, React, FastApi"
    r2 = b"Candidate Two\nEmail: c2@test.com\nPython, Django, Vue"

    u1 = await async_client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("c1.txt", io.BytesIO(r1), "text/plain")},
        data={"job_id": job_id},
    )
    c1_id = u1.json()["candidate_id"]

    u2 = await async_client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("c2.txt", io.BytesIO(r2), "text/plain")},
        data={"job_id": job_id},
    )
    c2_id = u2.json()["candidate_id"]

    # 4. Fetch Recruiter Candidate Cards
    cards_resp = await async_client.get(f"/api/v1/dashboard/job/{job_id}/candidates", headers=headers)
    assert cards_resp.status_code == 200
    cards = cards_resp.json()
    assert len(cards) == 2

    app_id = cards[0]["application_id"]

    # 5. Update Status (Shortlist Candidate)
    status_resp = await async_client.patch(
        f"/api/v1/dashboard/application/{app_id}/status",
        headers=headers,
        json={"status": "shortlisted", "notes": "Strong candidate for architecture role."},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "shortlisted"

    # 6. Side-by-Side Comparison
    comp_resp = await async_client.post(
        "/api/v1/dashboard/compare",
        headers=headers,
        json={"job_id": job_id, "candidate_ids": [c1_id, c2_id]},
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert len(comp_data["columns"]) == 2
    assert "recommended_top_candidate_id" in comp_data

    # 7. Submit Feedback
    fb_resp = await async_client.post(
        "/api/v1/dashboard/feedback",
        headers=headers,
        json={
            "job_id": job_id,
            "candidate_id": c1_id,
            "action": "shortlisted",
            "rating": 5.0,
            "feedback_text": "Top quality candidate.",
        },
    )
    assert fb_resp.status_code == 201
    assert fb_resp.json()["success"] is True
