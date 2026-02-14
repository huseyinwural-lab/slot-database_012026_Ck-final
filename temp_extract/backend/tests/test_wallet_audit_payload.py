import os
import sys

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))


from tests.conftest import _create_tenant, _create_player, _make_player_token
from app.models.sql_models import AuditEvent


@pytest.mark.usefixtures("client")
def test_audit_payload_for_withdraw_request(client, async_session_factory):
    async def seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=100)
            token = _make_player_token(player.id, tenant.id)
            return tenant, player, token

    import asyncio

    tenant, player, token = asyncio.run(seed())

    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "wd-audit-001"}
    r = client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 20, "method": "bank", "address": "addr"},
        headers=headers,
    )
    assert r.status_code in (200, 201)

    async def fetch_events():
        async with async_session_factory() as session:
            stmt = select(AuditEvent).where(AuditEvent.action == "FIN_WITHDRAW_REQUESTED")
            res = await session.execute(stmt)
            return res.scalars().all()

    events = asyncio.run(fetch_events())
    assert events, "No FIN_WITHDRAW_REQUESTED events found"

    evt = events[-1]
    details = evt.details or {}

    for key in [
        "tx_id",
        "player_id",
        "amount",
        "currency",
        "old_state",
        "new_state",
        "idempotency_key",
        "request_id",
        "balance_available_before",
        "balance_available_after",
        "balance_held_before",
        "balance_held_after",
    ]:
        assert key in details, f"Missing {key} in audit details"
