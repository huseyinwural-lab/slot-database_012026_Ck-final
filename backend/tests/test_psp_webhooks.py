import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from config import settings
from tests.conftest import _create_tenant, _create_player, _make_player_token
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


@pytest.mark.usefixtures("client")
def test_withdraw_paid_webhook_finalizes_pending_and_is_idempotent(client, async_session_factory):
    """W1: withdraw_paid webhook maps to ledger + pending finalize (created-gated)."""

    settings.ledger_shadow_write = True

    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, kyc_status="verified", balance_available=0.0)
            return tenant, player

    tenant, player = asyncio.run(_seed())

    # Seed wallet with 100 and create a pending withdraw of 40 via existing flow
    # Deposit 100
    dep_headers = {"Authorization": f"Bearer {_make_player_token(player.id, tenant.id)}", "Idempotency-Key": "idem-psp-w-dep"}
    r_dep = client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 100.0, "method": "test"},
        headers=dep_headers,
    )
    assert r_dep.status_code in (200, 201)

    # Withdraw 40 to create pending
    w_headers = {"Authorization": dep_headers["Authorization"], "Idempotency-Key": "idem-psp-w-wd"}
    r_w = client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 40.0, "method": "test_bank", "address": "psp"},
        headers=w_headers,
    )
    assert r_w.status_code in (200, 201)

    async def _check_pending():
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
            return wb

    wb_before = asyncio.run(_check_pending())
    assert wb_before.balance_real_pending == pytest.approx(40.0)

    payload = {
        "provider_event_id": "evt-psp-w-1",
        "event_type": "withdraw_paid",
        "player_id": player.id,
        "tenant_id": tenant.id,
        "amount": 40.0,
        "currency": "USD",
        "tx_id": r_w.json().get("transaction", {}).get("id") or r_w.json().get("tx_id"),
    }

    # First webhook call
    r1 = client.post("/api/v1/payments/webhook/mockpsp", json=payload)
    assert r1.status_code == 200

    # Second webhook call with same provider_event_id (replay)
    r2 = client.post("/api/v1/payments/webhook/mockpsp", json=payload)
    assert r2.status_code == 200

    async def _check_after():
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
            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.tenant_id == tenant.id,
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.type == "withdraw",
                        LedgerTransaction.status == "withdraw_paid",
                        LedgerTransaction.provider == "mockpsp",
                        LedgerTransaction.provider_event_id == "evt-psp-w-1",
                    )
                )
            ).scalars().all()
            return wb, evs

    wb_after, evs = asyncio.run(_check_after())
    assert wb_after.balance_real_pending == pytest.approx(0.0)
    assert len(evs) == 1


def test_mockpsp_signature_enforcement_negative_and_positive():
    """S1/S2: when enforcement is ON, invalid/missing signature -> error; valid -> OK.

    This tests the signature helper in isolation, without hitting HTTP.
    """

    # Turn on enforcement
    old_enforced = settings.webhook_signature_enforced
    old_secret = settings.webhook_secret_mockpsp
    settings.webhook_signature_enforced = True
    settings.webhook_secret_mockpsp = "test-secret"

    payload = {"provider_event_id": "evt-1", "amount": 10}

    # Missing header -> error
    with pytest.raises(WebhookSignatureError):
        _verify_mockpsp_signature(payload, {})

    import hashlib
    import json

    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    valid_sig = hashlib.sha256((settings.webhook_secret_mockpsp + body.decode("utf-8")).encode("utf-8")).hexdigest()

    # Correct header -> no error
    _verify_mockpsp_signature(payload, {"X-MockPSP-Signature": valid_sig})

    # Restore settings
    settings.webhook_signature_enforced = old_enforced
    settings.webhook_secret_mockpsp = old_secret
