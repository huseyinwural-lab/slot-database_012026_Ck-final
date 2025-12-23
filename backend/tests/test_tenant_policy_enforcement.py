import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
import uuid

from app.models.sql_models import Transaction, PayoutAttempt, Tenant

@pytest.mark.asyncio
async def test_payout_retry_policy_enforcement(async_client: AsyncClient, admin_token_headers, session, test_tenant):
    # Setup Tenant Policy
    test_tenant.payout_retry_limit = 2
    test_tenant.payout_cooldown_seconds = 5
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
    assert resp.status_code == 200
    
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
    await asyncio.sleep(6) # 5s + buffer

    # Attempt 2: Success (after cooldown)
    resp = await async_client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        headers=admin_token_headers,
        json={"reason": "Retrying second time"}
    )
    assert resp.status_code == 200

    # Attempt 3: Blocked by Limit (Limit is 2, we have 2 existing attempts now)
    await asyncio.sleep(6) # Ensure cooldown is not the blocker
    resp = await async_client.post(
        f"/api/v1/finance-actions/withdrawals/{tx.id}/retry",
        headers=admin_token_headers,
        json={"reason": "Retrying third time"}
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "PAYMENT_RETRY_LIMIT_EXCEEDED"
