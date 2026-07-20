import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_semantic_skill_matching(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Semantic HR",
            "company_slug": "semantic-hr",
            "full_name": "Alice HR",
            "email": "alice@semantichr.com",
            "password": "Password123!",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@semantichr.com", "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Semantic Matching (Power BI vs Microsoft BI, DAX)
    match_payload = {
        "required_skills": ["Power BI", "People Analytics"],
        "candidate_skills": ["Microsoft BI", "DAX", "HR Analytics", "PowerQuery"],
        "candidate_experience_text": "Built executive dashboards using Microsoft BI, DAX formulas, and led HR Analytics workforce reporting.",
    }
    response = await async_client.post(
        "/api/v1/intelligence/semantic-skill-match",
        headers=headers,
        json=match_payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert "semantic_matches" in data
    assert data["overall_semantic_score"] >= 80.0
    matches = {m["required_skill"]: m for m in data["semantic_matches"]}
    assert matches["Power BI"]["match_type"] in ["EXACT", "SEMANTIC", "CONCEPTUAL"]
    assert matches["People Analytics"]["match_type"] in ["EXACT", "SEMANTIC", "CONCEPTUAL"]

    # 3. Test Vector Embedding Generation
    embed_resp = await async_client.post(
        "/api/v1/intelligence/embed-text?text=Power+BI",
        headers=headers,
    )
    assert embed_resp.status_code == 200
    assert "embedding" in embed_resp.json()
    assert len(embed_resp.json()["embedding"]) > 0
