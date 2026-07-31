import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import text
from app.core.database import get_db

@pytest.mark.asyncio
async def test_tenant_isolation_and_governance(async_client: AsyncClient):
    # Generate unique test keys to prevent DB unique key constraint (409 Conflict) collisions
    rand = str(uuid.uuid4())[:8]
    company_slug_a = f"company-alpha-{rand}"
    email_a = f"alice-{rand}@alpha.com"
    company_slug_b = f"company-beta-{rand}"
    email_b = f"bob-{rand}@beta.com"

    # 1. Register Tenant A (Company A) & get token
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "company_name": f"Company Alpha {rand}",
        "company_slug": company_slug_a,
        "full_name": "Alice Admin",
        "email": email_a,
        "password": "SecurePassword123!",
    })
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user"]["id"]
    company_a_id = reg_a.json()["user"]["company_id"]

    # 2. Register Tenant B (Company B) & get token
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "company_name": f"Company Beta {rand}",
        "company_slug": company_slug_b,
        "full_name": "Bob Admin",
        "email": email_b,
        "password": "SecurePassword123!",
    })
    assert reg_b.status_code == 201
    token_b = reg_b.json()["access_token"]

    # 3. Create a candidate in Company A directly inside the DB to simulate ingestion
    async for db in get_db():
        cand_id = str(uuid.uuid4())
        await db.execute(
            text("""
                INSERT INTO candidates (id, company_id, full_name, email, is_internal)
                VALUES (:id, :comp, :name, :email, 0)
            """),
            {"id": cand_id, "comp": company_a_id, "name": "Secret Candidate", "email": "secret@candidate.com"}
        )
        await db.commit()
        break

    # 4. Attempt to erase Company A's candidate using Company B's token (Cross-tenant attack)
    erase_headers = {"Authorization": f"Bearer {token_b}"}
    erase_fail = await async_client.post(
        f"/api/v1/governance/gdpr/erase/{cand_id}",
        headers=erase_headers
    )
    # The endpoint check should reject this cross-tenant request or return forbidden
    assert erase_fail.status_code == 403

    # 5. Erase the candidate using Company A's own admin token (Correct access)
    erase_success_headers = {"Authorization": f"Bearer {token_a}"}
    erase_ok = await async_client.post(
        f"/api/v1/governance/gdpr/erase/{cand_id}",
        headers=erase_success_headers
    )
    assert erase_ok.status_code == 200
    assert erase_ok.json()["erased"] is True

    # 6. Verify candidate has been purged from the database
    async for db in get_db():
        check_cand = await db.execute(
            text("SELECT * FROM candidates WHERE id = :id"),
            {"id": cand_id}
        )
        assert check_cand.fetchone() is None
        break
