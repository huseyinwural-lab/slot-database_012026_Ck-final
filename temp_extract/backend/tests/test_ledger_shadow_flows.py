import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from config import settings
from tests.conftest import _create_tenant, _create_player, _make_player_token
from app.models.sql_models import Player
from app.repositories.ledger_repo import LedgerTransaction, WalletBalance


@pytest.mark.usefixtures("client")
def test_withdraw_requested_creates_hold_in_player_and_ledger(client, async_session_factory):
    settings.ledger_shadow_write = True

    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            # Start with zero balance in DB; fund via deposit so ledger snapshot sees it
            player = await _create_player(session, tenant.id, balance_available=0.0, kyc_status="verified")
            token = _make_player_token(player.id, tenant.id)

        # Fund via deposit so both player and ledger start from 100 available
        dep_headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-deposit-1"}
        r_dep = client.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 100.0, "method": "test"},
            headers=dep_headers,
        )
        assert r_dep.status_code in (200, 201)

        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-withdraw-1"}
        r = client.post(
            "/api/v1/player/wallet/withdraw",
            json={"amount": 10.0, "method": "test_bank", "address": "e2e"},
            headers=headers,
        )
        assert r.status_code in (200, 201)

        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            assert db_player.balance_real_available == pytest.approx(90.0)
            assert db_player.balance_real_held == pytest.approx(10.0)

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
            assert wb.balance_real_available == pytest.approx(90.0)
            assert wb.balance_real_pending == pytest.approx(10.0)

            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.status == "withdraw_requested",
                        LedgerTransaction.idempotency_key == "idem-withdraw-1",
                    )
                )
            ).scalars().all()
            assert len(evs) == 1

    asyncio.run(_run())


@pytest.mark.usefixtures("client")
def test_withdraw_idempotent_request_does_not_double_apply_hold(client, async_session_factory):
    settings.ledger_shadow_write = True

    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, balance_available=0.0, kyc_status="verified")
            token = _make_player_token(player.id, tenant.id)

        # Fund via deposit so both player and ledger start from 100 available
        dep_headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-deposit-2"}
        r_dep = client.post(
            "/api/v1/player/wallet/deposit",
            json={"amount": 100.0, "method": "test"},
            headers=dep_headers,
        )
        assert r_dep.status_code in (200, 201)

        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-withdraw-dup"}
        payload = {"amount": 10.0, "method": "test_bank", "address": "e2e"}

        r1 = client.post("/api/v1/player/wallet/withdraw", json=payload, headers=headers)
        assert r1.status_code in (200, 201)
        r2 = client.post("/api/v1/player/wallet/withdraw", json=payload, headers=headers)
        assert r2.status_code in (200, 201)

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
            assert wb.balance_real_available == pytest.approx(90.0)
            assert wb.balance_real_pending == pytest.approx(10.0)

            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.status == "withdraw_requested",
                        LedgerTransaction.idempotency_key == "idem-withdraw-dup",
                    )
                )
            ).scalars().all()
            assert len(evs) == 1

    asyncio.run(_run())


# NOTE: Additional tests for reject / paid flows would follow the same pattern,
# but involve admin seeding and calling the finance admin endpoints to transition
# states and then asserting WalletBalance + LedgerTransaction contents.
