import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_job_description_parsing_and_creation(async_client: AsyncClient):
    # 1. Register and Login to get Auth Token
    reg_payload = {
        "company_name": "TechStaff Corp",
        "company_slug": "techstaff",
        "full_name": "Sarah Recruiter",
        "email": "sarah@techstaff.com",
        "password": "Password123!",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "sarah@techstaff.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test AI JD Raw Text Parsing
    jd_text = """
    We are hiring a Senior Full Stack Engineer with 5+ years of experience.
    Mandatory Skills: Python, FastAPI, React, PostgreSQL.
    Good to have: Docker, AWS, Power BI.
    Education: Bachelor's in CS.
    Location: San Francisco (Remote option available).
    Salary: $120,000 - $160,000 USD.
    """
    parse_resp = await async_client.post(
        "/api/v1/jobs/parse-text",
        headers=headers,
        json={"raw_description": jd_text},
    )
    assert parse_resp.status_code == 200
    extract_data = parse_resp.json()
    assert "role" in extract_data
    assert "mandatory_skills" in extract_data

    # 3. Save Job Posting
    save_payload = {
        "title": extract_data["role"],
        "department": "Engineering",
        "raw_description": jd_text,
        "status": "active",
        "min_experience_years": extract_data["min_experience_years"],
        "max_experience_years": extract_data["max_experience_years"],
        "education_requirement": extract_data["education_requirement"],
        "location": extract_data["location"],
        "is_remote": extract_data["is_remote"],
        "min_salary": extract_data["min_salary"],
        "max_salary": extract_data["max_salary"],
        "salary_currency": extract_data["salary_currency"],
        "responsibilities": extract_data["responsibilities"],
        "mandatory_skills": extract_data["mandatory_skills"],
        "good_to_have_skills": extract_data["good_to_have_skills"],
    }
    create_resp = await async_client.post("/api/v1/jobs/", headers=headers, json=save_payload)
    assert create_resp.status_code == 201
    job_data = create_resp.json()
    job_id = job_data["id"]
    assert len(job_data["job_skills"]) > 0

    # 4. List Company Jobs
    list_resp = await async_client.get("/api/v1/jobs/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 5. Get Single Job Details
    get_resp = await async_client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id
