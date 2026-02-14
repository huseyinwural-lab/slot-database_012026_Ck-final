import os
import sys
from decimal import Decimal

import pytest
# Async client is provided via the shared `client` fixture in conftest.

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.sql_models import Tenant  # noqa: E402


@pytest.mark.asyncio
async def test_deposit_limit_exceeded_returns_422(client, player_with_token, async_session_factory):
    tenant, player, player_token = player_with_token
    # Set tenant daily_deposit_limit = 50 in the same test DB
    async with async_session_factory() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        assert db_tenant is not None
        db_tenant.daily_deposit_limit = Decimal("50.0")
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "k2"}

    # Seed usage by inserting a completed deposit of 40 directly (simulate PSP success)
    async with async_session_factory() as session:
        from app.models.sql_models import Transaction
        from datetime import datetime, timezone

        tx = Transaction(
            tenant_id=tenant.id,
            player_id=player.id,
            type="deposit",
            amount=40.0,
            currency="USD",
            status="completed",
            state="completed",
            method="test",
            idempotency_key="seed-dep-40",
            created_at=datetime.now(timezone.utc),
            balance_after=0.0,
        )
        session.add(tx)
        await session.commit()

    # Deposit 20 should now fail because limit 50 is exceeded (40 + 20)
    res2 = await client.post(
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


@pytest.mark.asyncio
async def test_withdraw_limit_exceeded_returns_422(client, player_with_token, async_session_factory):
    tenant, player, player_token = player_with_token
    # Set tenant daily_withdraw_limit = 30 in the same test DB
    async with async_session_factory() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        assert db_tenant is not None
        db_tenant.daily_withdraw_limit = Decimal("30.0")
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "w2"}

    # Seed usage by inserting a requested withdrawal of 20 directly
    async with async_session_factory() as session:
        from app.models.sql_models import Transaction
        from datetime import datetime, timezone

        tx = Transaction(
            tenant_id=tenant.id,
            player_id=player.id,
            type="withdrawal",
            amount=20.0,
            currency="USD",
            status="pending",
            state="requested",
            method="crypto",
            idempotency_key="seed-wd-20",
            created_at=datetime.now(timezone.utc),
            balance_after=0.0,
        )
        session.add(tx)
        await session.commit()

    res2 = await client.post(
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


@pytest.mark.asyncio
async def test_no_policy_allows_transactions(client, player_with_token, async_session_factory):
    tenant, player, player_token = player_with_token
    # Ensure policy fields are None in the same test DB
    async with async_session_factory() as session:
        db_tenant = await session.get(Tenant, tenant.id)
        assert db_tenant is not None
        db_tenant.daily_deposit_limit = None
        db_tenant.daily_withdraw_limit = None
        session.add(db_tenant)
        await session.commit()

    headers = {"Authorization": f"Bearer {player_token}", "Content-Type": "application/json", "Idempotency-Key": "np1"}

    res1 = await client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 100.0, "method": "test"},
        headers=headers,
    )
    assert res1.status_code in (200, 201)

    headers["Idempotency-Key"] = "np2"
    res2 = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 80.0, "method": "crypto", "address": "addr"},
        headers=headers,
    )
    assert res2.status_code in (200, 201)
