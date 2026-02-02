import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from tests.conftest import _create_tenant, _create_player
from app.models.sql_models import Transaction, AuditEvent


@pytest.mark.usefixtures("client")
def test_webhook_idempotency(client, async_session_factory):
    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=0)
            return tenant, player

    tenant, player = asyncio.run(_seed())

    payload = {
        "provider_event_id": "evt-123",
        "player_id": player.id,
        "tenant_id": tenant.id,
        "amount": 50,
        "currency": "USD",
        "type": "deposit",
    }

    # First call -> creates transaction and FIN_WEBHOOK_RECEIVED
    r1 = client.post("/api/v1/payments/webhook/mock", json=payload)
    assert r1.status_code == 200

    # Second call with same provider_event_id -> no-op + FIN_IDEMPOTENCY_HIT
    r2 = client.post("/api/v1/payments/webhook/mock", json=payload)
    assert r2.status_code == 200

    async def _check_db():
        async with async_session_factory() as session:
            # Only count transactions created by this webhook provider/event
            txs = (
                await session.execute(
                    select(Transaction).where(
                        Transaction.provider == "mock",
                        Transaction.provider_event_id == "evt-123",
                    )
                )
            ).scalars().all()

            events = (await session.execute(select(AuditEvent))).scalars().all()
            return txs, events

    txs, events = asyncio.run(_check_db())
    # Exactly one transaction for this provider_event_id
    assert len(txs) == 1
    actions = [e.action for e in events]
    assert "FIN_WEBHOOK_RECEIVED" in actions
    assert "FIN_IDEMPOTENCY_HIT" in actions
