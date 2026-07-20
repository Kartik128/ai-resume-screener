import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tenant_registration_and_login(async_client: AsyncClient):
    # 1. Register Tenant Company & Admin
    reg_payload = {
        "company_name": "Acme HR Corp",
        "company_slug": "acme-hr",
        "full_name": "John Admin",
        "email": "admin@acmehr.com",
        "password": "SecurePassword123!",
    }
    response = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "admin@acmehr.com"
    assert data["user"]["role"] == "admin"

    # 2. Login with registered user
    login_payload = {
        "email": "admin@acmehr.com",
        "password": "SecurePassword123!",
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 3. Get /me user profile with Bearer Token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "admin@acmehr.com"

    # 4. Refresh access token
    ref_resp = await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert ref_resp.status_code == 200
    assert "access_token" in ref_resp.json()


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 403 or response.status_code == 401
