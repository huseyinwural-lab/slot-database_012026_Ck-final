import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.models.sql_models import Transaction
from sqlmodel import select

@pytest.mark.asyncio
async def test_payout_provider_mock_gated_in_prod(client: AsyncClient, admin_token, session):
    """
    Ensure mock payouts are gated in production.
    """
    # 0. Get Tenant ID from Admin Token (or DB)
    from app.models.sql_models import Tenant
    stmt = select(Tenant)
    tenant = (await session.execute(stmt)).scalars().first()
    assert tenant is not None
    tenant_id = tenant.id

    # 1. Create a withdrawal
    tx = Transaction(
        tenant_id=tenant_id,
        player_id="player1",
        type="withdrawal",
        amount=50.0,
        currency="USD",
        status="pending",
        state="approved",
        provider="mock_psp"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    # 2. Attempt Retry in PROD
    with patch("config.settings.env", "prod"):
        with patch("config.settings.allow_test_payment_methods", False):
            resp = await client.post(
                f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
                json={"reason": "Retrying"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert resp.status_code == 403
            assert "Mock payouts are disabled" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_payout_provider_mock_allowed_in_dev(client: AsyncClient, admin_token, session):
    """
    Ensure mock payouts work in dev.
    """
    # 0. Get Tenant ID
    from app.models.sql_models import Tenant
    stmt = select(Tenant)
    tenant = (await session.execute(stmt)).scalars().first()
    assert tenant is not None
    tenant_id = tenant.id

    tx = Transaction(
        tenant_id=tenant_id,
        player_id="player2",
        type="withdrawal",
        amount=50.0,
        currency="USD",
        status="pending",
        state="approved",
        provider="mock_psp"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    resp = await client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        json={"reason": "Retrying"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "retry_initiated"
