import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_and_export_reports(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Analytics Corp",
            "company_slug": "analytics-corp",
            "full_name": "VP HR",
            "email": "vp@analyticscorp.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "vp@analyticscorp.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test HR Analytics Dashboard Overview
    overview_resp = await async_client.get("/api/v1/analytics/overview", headers=headers)
    assert overview_resp.status_code == 200
    ov_data = overview_resp.json()
    assert "hiring_funnel" in ov_data
    assert "top_candidate_skills" in ov_data
    assert len(ov_data["hiring_funnel"]) > 0

    # 3. Create Job and Candidate for Export Testing
    job_resp = await async_client.post(
        "/api/v1/jobs/",
        headers=headers,
        json={"title": "Data Engineer", "raw_description": "SQL Python ETL"},
    )
    job_id = job_resp.json()["id"]

    res_bytes = b"Dave Engineer\nEmail: dave@test.com\nPython, SQL, ETL"
    up_resp = await async_client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("dave.txt", io.BytesIO(res_bytes), "text/plain")},
        data={"job_id": job_id},
    )
    cand_id = up_resp.json()["candidate_id"]

    # Evaluate score to ensure export data exists
    await async_client.post(f"/api/v1/scoring/evaluate/{job_id}/{cand_id}", headers=headers)

    # 4. Test CSV Export
    csv_resp = await async_client.get(f"/api/v1/exports/job/{job_id}/csv", headers=headers)
    assert csv_resp.status_code == 200
    assert "Candidate Name" in csv_resp.text

    # 5. Test Excel Export
    excel_resp = await async_client.get(f"/api/v1/exports/job/{job_id}/excel", headers=headers)
    assert excel_resp.status_code == 200
    assert len(excel_resp.content) > 0

    # 6. Test PDF Export
    pdf_resp = await async_client.get(f"/api/v1/exports/candidate/{cand_id}/job/{job_id}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert len(pdf_resp.content) > 0
