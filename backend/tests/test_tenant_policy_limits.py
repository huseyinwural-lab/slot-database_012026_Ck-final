import os
import sys
from decimal import Decimal

import pytest
# Async client is provided via the shared `client` fixture in conftest.

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server import app  # noqa: E402
from app.core.database import async_session  # noqa: E402
from app.models.sql_models import Tenant  # noqa: E402
from app.services.tenant_policy_enforcement import ensure_within_tenant_daily_limits  # noqa: E402


@pytest.mark.asyncio
async def test_deposit_limit_exceeded_returns_422(client, player_with_token):
    tenant, player, player_token = player_with_token
    # Set tenant daily_deposit_limit = 50
    async with async_session() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        db_tenant.daily_deposit_limit = Decimal("50.0")
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "k1"}

    # First deposit 40 (ok)
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res1 = await ac.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 40.0, "method": "test"},
            headers=headers,
        )
        assert res1.status_code in (200, 201)

    # Second deposit 20 (should fail, used_today ~40, limit 50)
    headers["Idempotency-Key"] = "k2"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res2 = await ac.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 20.0, "method": "test"},
            headers=headers,
        )

    assert res2.status_code == 422
    body = res2.json()["detail"]
    assert body["error_code"] == "LIMIT_EXCEEDED"
    assert body["scope"] == "tenant_daily"
    assert body["action"] == "deposit"
    assert body["limit"] == pytest.approx(50.0)
    assert body["used_today"] == pytest.approx(40.0, rel=1e-2)
    assert body["attempted"] == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_withdraw_limit_exceeded_returns_422(client, tenant, player_token):
    # Set tenant daily_withdraw_limit = 30
    async with async_session() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        db_tenant.daily_withdraw_limit = Decimal("30.0")
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "w1"}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res1 = await ac.post(
            "/api/v1/player/wallet/withdraw",
            json={"amount": 20.0, "method": "crypto", "address": "addr1"},
            headers=headers,
        )
        assert res1.status_code in (200, 201)

    headers["Idempotency-Key"] = "w2"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res2 = await ac.post(
            "/api/v1/player/wallet/withdraw",
            json={"amount": 15.0, "method": "crypto", "address": "addr2"},
            headers=headers,
        )

    assert res2.status_code == 422
    body = res2.json()["detail"]
    assert body["error_code"] == "LIMIT_EXCEEDED"
    assert body["scope"] == "tenant_daily"
    assert body["action"] == "withdraw"
    assert body["limit"] == pytest.approx(30.0)
    assert body["used_today"] == pytest.approx(20.0, rel=1e-2)
    assert body["attempted"] == pytest.approx(15.0)


@pytest.mark.asyncio
async def test_no_policy_allows_transactions(client, tenant, player_token):
    # Ensure policy fields are None
    async with async_session() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        db_tenant.daily_deposit_limit = None
        db_tenant.daily_withdraw_limit = None
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "np1"}

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res1 = await ac.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 100.0, "method": "test"},
            headers=headers,
        )
        assert res1.status_code in (200, 201)

    headers["Idempotency-Key"] = "np2"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res2 = await ac.post(
            "/api/v1/player/wallet/withdraw",
            json={"amount": 80.0, "method": "crypto", "address": "addr"},
            headers=headers,
        )
        assert res2.status_code in (200, 201)
