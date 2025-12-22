import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from config import settings
from tests.conftest import _create_tenant, _create_player
from app.repositories.ledger_repo import LedgerTransaction, WalletBalance
from app.services.psp.webhook_parser import _verify_mockpsp_signature, WebhookSignatureError


@pytest.mark.usefixtures("client")
def test_webhook_replay_guard_and_ledger_mapping_for_deposit(client, async_session_factory):
    """PSP-02E: Deposit webhook -> ledger events + replay guard.

    - First webhook call should append a single deposit ledger event and apply
      delta once (created-gated).
    - Second call with same provider_event_id is a no-op at ledger level.
    """

    settings.ledger_shadow_write = True

    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=0.0)
            return tenant, player

    tenant, player = asyncio.run(_seed())

    payload = {
        "provider_event_id": "evt-psp-dep-1",
        "event_type": "deposit_captured",
        "player_id": player.id,
        "tenant_id": tenant.id,
        "amount": 30.0,
        "currency": "USD",
        "tx_id": "tx-psp-dep-1",
    }

    # First call -> ledger event + delta
    r1 = client.post("/api/v1/payments/webhook/mockpsp", json=payload)
    assert r1.status_code == 200

    # Second call with same provider_event_id -> idempotent no-op in ledger
    r2 = client.post("/api/v1/payments/webhook/mockpsp", json=payload)
    assert r2.status_code == 200

    async def _check():
        async with async_session_factory() as session:
            wb = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant.id,
                        WalletBalance.player_id == player.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()
            assert wb is not None
            assert wb.balance_real_available == pytest.approx(30.0)
            assert wb.balance_real_pending == pytest.approx(0.0)

            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.tenant_id == tenant.id,
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.type == "deposit",
                        LedgerTransaction.status == "deposit_captured",
                        LedgerTransaction.provider == "mockpsp",
                        LedgerTransaction.provider_event_id == "evt-psp-dep-1",
                    )
                )
            ).scalars().all()
            assert len(evs) == 1

    asyncio.run(_check())
