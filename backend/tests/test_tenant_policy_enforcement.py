import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid

from app.models.sql_models import Transaction
from app.core.database import get_session
from server import app
# Import directly from tests.conftest - workaround for module resolution in this env
from tests.conftest import make_override_get_session, _create_tenant, _create_admin, _make_admin_token

# Use pytest-asyncio strict mode compatibility
@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest_asyncio.fixture(scope="function")
async def async_client(async_session_factory):
    app.dependency_overrides[get_session] = make_override_get_session(async_session_factory)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def session(async_session_factory):
    async with async_session_factory() as s:
        yield s

@pytest_asyncio.fixture(scope="function")
async def test_tenant(session):
    return await _create_tenant(session, name="PolicyTenant_" + str(uuid.uuid4()))

@pytest_asyncio.fixture(scope="function")
async def admin_token_headers(session, test_tenant):
    admin = await _create_admin(session, tenant_id=test_tenant.id, email=f"admin_{uuid.uuid4()}@test.com")
    token = _make_admin_token(admin.id, test_tenant.id, admin.email)
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_payout_retry_policy_enforcement(async_client, admin_token_headers, session, test_tenant):
    # Setup Tenant Policy
    test_tenant.payout_retry_limit = 2
    test_tenant.payout_cooldown_seconds = 2
    session.add(test_tenant)
    await session.commit()
    await session.refresh(test_tenant)

    # Create Transaction
    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=test_tenant.id,
        player_id="player1",
        type="withdrawal",
        amount=100.0,
        status="failed",
        state="failed"
    )
    session.add(tx)
    await session.commit()

    # Attempt 1: Success
    resp = await async_client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        headers=admin_token_headers,
        json={"reason": "Retrying first time"}
    )
    assert resp.status_code == 200, resp.text
    
    # Attempt 2: Blocked by Cooldown
    resp = await async_client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        headers=admin_token_headers,
        json={"reason": "Retrying too fast"}
    )
    assert resp.status_code == 429
    assert resp.json()["detail"]["error_code"] == "PAYMENT_COOLDOWN_ACTIVE"

    # Wait for cooldown
    import asyncio
    await asyncio.sleep(2.5) 

    # Attempt 2: Success (after cooldown)
    resp = await async_client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        headers=admin_token_headers,
        json={"reason": "Retrying second time"}
    )
    assert resp.status_code == 200

    # Attempt 3: Blocked by Limit (Limit is 2, we have 2 existing attempts now)
    await asyncio.sleep(2.5) # Ensure cooldown is not the blocker
    resp = await async_client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        headers=admin_token_headers,
        json={"reason": "Retrying third time"}
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "PAYMENT_RETRY_LIMIT_EXCEEDED"
