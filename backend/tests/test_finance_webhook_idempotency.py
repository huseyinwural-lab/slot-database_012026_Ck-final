import os, sys

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from fastapi.testclient import TestClient

from server import app
from tests.conftest import async_session_factory, _create_tenant, _create_player
from app.models.sql_models import Transaction, AuditEvent


def _make_client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_webhook_idempotency(async_session_factory):
    client = _make_client()

    async with async_session_factory() as session:
        tenant = await _create_tenant(session)
        player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=0)

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

    async with async_session_factory() as session:
        txs = (await session.execute(select(Transaction))).scalars().all()
        assert len(txs) == 1

        events = (await session.execute(select(AuditEvent))).scalars().all()
        actions = [e.action for e in events]
        assert "FIN_WEBHOOK_RECEIVED" in actions
        assert "FIN_IDEMPOTENCY_HIT" in actions
