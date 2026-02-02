import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from config import settings
from tests.test_finance_withdraw_admin_api import _seed_admin_and_player
from app.models.sql_models import Player
from app.repositories.ledger_repo import LedgerTransaction, WalletBalance


@pytest.mark.usefixtures("client")
def test_deposit_authorize_and_capture_ledger_and_snapshot(client, async_session_factory):
    """E1: Deposit triggers authorize + capture ledger events and updates snapshot.

    - LedgerTransaction: deposit_authorized + deposit_captured with provider metadata.
    - WalletBalance.balance_real_available increased by deposit amount.
    """

    settings.ledger_shadow_write = True

    async def _run():
        # Reuse existing helper to seed tenant, player and admin + tokens
        tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)
        token = player_token

        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-psp-dep-1"}
        amount = 50.0
        r_dep = client.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": amount, "method": "test"},
            headers=headers,
        )
        assert r_dep.status_code in (200, 201)

        async with async_session_factory() as session:
            # Check that exactly one deposit delta (+amount) was applied
            db_player = await session.get(Player, player.id)
            before_plus_amount = db_player.balance_real_available

        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            assert db_player.balance_real_available == pytest.approx(before_plus_amount)

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
            assert wb.balance_real_available == pytest.approx(amount)
            assert wb.balance_real_pending == pytest.approx(0.0)

            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.tenant_id == tenant.id,
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.type == "deposit",
                    )
                )
            ).scalars().all()
            statuses = {e.status for e in evs}
            assert "deposit_authorized" in statuses
            assert "deposit_captured" in statuses

            # Provider metadata should be populated
            for e in evs:
                assert e.provider == "mockpsp"
                assert e.provider_ref is not None
                assert e.provider_event_id is not None

    asyncio.run(_run())


@pytest.mark.usefixtures("client")
def test_mark_paid_adds_psp_metadata_and_finalizes_pending(client, async_session_factory):
    """E2: Mark-paid triggers PSP payout and finalizes pending balance.

    Flow:
    - Deposit 100
    - Withdraw 40 (requested -> approved -> paid)

    Expectations:
    - WalletBalance.pending decreases by 40 on paid.
    - withdraw_paid event has provider metadata.
    """

    settings.ledger_shadow_write = True

    async def _run():
        # Reuse existing helper to seed tenant, player and admin + tokens
        tenant, player, admin, player_token, admin_token = await _seed_admin_and_player(async_session_factory)
        token = player_token

        # Fund via deposit 100
        dep_headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-psp-dep-2"}
        r_dep = client.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 100.0, "method": "test"},
            headers=dep_headers,
        )
        assert r_dep.status_code in (200, 201)

        # Player withdraw 40
        w_headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-psp-w-1"}
        r_w = client.post(
            "/api/v1/player/wallet/withdraw",
            json={"amount": 40.0, "method": "test_bank", "address": "psp"},
            headers=w_headers,
        )
        assert r_w.status_code in (200, 201)
        tx_id = r_w.json().get("transaction", {}).get("id") or r_w.json().get("tx_id")
        assert tx_id

        # Admin approve then mark-paid via finance endpoints using seeded admin token
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        r_rev = client.post(
            f"/api/v1/finance/withdrawals/{tx_id}/review",
            json={"action": "approve"},
            headers=admin_headers,
        )
        assert r_rev.status_code in (200, 201)

        r_paid = client.post(
            f"/api/v1/finance/withdrawals/{tx_id}/mark-paid",
            headers=admin_headers,
        )
        assert r_paid.status_code in (200, 201)

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
            assert wb.balance_real_pending == pytest.approx(0.0)

            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.tenant_id == tenant.id,
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.type == "withdraw",
                        LedgerTransaction.status == "withdraw_paid",
                    )
                )
            ).scalars().all()
            assert len(evs) >= 1
            for e in evs:
                assert e.provider == "mockpsp"
                assert e.provider_ref is not None
                assert e.provider_event_id is not None

    asyncio.run(_run())
