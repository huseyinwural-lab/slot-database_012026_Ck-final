from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.repositories.ledger_repo import WalletBalance, LedgerTransaction
from app.models.sql_models import Player, Transaction
from sqlalchemy import select


@pytest.mark.usefixtures("client", "player_with_token")
@pytest.mark.asyncio
async def test_deposit_success_updates_wallet_and_ledger(client: AsyncClient, async_session_factory, player_with_token):
    tenant, player, token = player_with_token

    # No initial snapshot
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
        assert wb is None

    headers = {"Idempotency-Key": "idem-dep-success", "Authorization": f"Bearer {token}"}
    r = await client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 50.0, "method": "test"},
        headers=headers,
    )
    assert r.status_code in (200, 201)

    async with async_session_factory() as session:
        # Player balances
        player_db = await session.get(Player, player.id)
        assert player_db is not None
        # Deposit funding is now driven by wallet_ledger; for this test we only
        # assert on the authoritative WalletBalance + ledger entries.
        # Player aggregate fields are validated by separate invariant tests.
        assert player_db.balance_real_held == pytest.approx(0.0)

        # WalletBalance snapshot
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
        assert wb.balance_real_available == pytest.approx(50.0)
        assert wb.balance_real_pending == pytest.approx(0.0)

        # LedgerTransaction event
        tx = (
            await session.execute(
                select(Transaction).where(
                    Transaction.tenant_id == tenant.id,
                    Transaction.player_id == player.id,
                    Transaction.type == "deposit",
                )
            )
        ).scalars().first()
        assert tx is not None

        evs = (
            await session.execute(
                select(LedgerTransaction).where(
                    LedgerTransaction.player_id == player.id,
                    LedgerTransaction.status == "deposit_succeeded",
                    LedgerTransaction.tx_id == str(tx.id),
                )
            )
        ).scalars().all()
        assert len(evs) == 1


@pytest.mark.usefixtures("client", "player_with_token")
@pytest.mark.asyncio
async def test_deposit_fail_outcome_has_net_zero_effect(client: AsyncClient, async_session_factory, player_with_token):
    tenant, player, token = player_with_token

    # Initial Player balance and no snapshot
    async with async_session_factory() as session:
        player_db = await session.get(Player, player.id)
        assert player_db is not None
        starting_available = float(player_db.balance_real_available)
        starting_held = float(player_db.balance_real_held)

        wb = (
            await session.execute(
                select(WalletBalance).where(
                    WalletBalance.tenant_id == tenant.id,
                    WalletBalance.player_id == player.id,
                    WalletBalance.currency == "USD",
                )
            )
        ).scalars().first()
        starting_wb_available = float(wb.balance_real_available) if wb else 0.0
        starting_wb_pending = float(wb.balance_real_pending) if wb else 0.0

    headers = {
        "Idempotency-Key": "idem-dep-fail",
        "Authorization": f"Bearer {token}",
        "X-Mock-Outcome": "fail",
    }
    r = await client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 30.0, "method": "test"},
        headers=headers,
    )
    # Even on PSP fail we expect HTTP 200/201 but net-zero balance change
    assert r.status_code in (200, 201)

    async with async_session_factory() as session:
        player_db = await session.get(Player, player.id)
        assert player_db is not None
        assert player_db.balance_real_available == pytest.approx(starting_available)
        assert player_db.balance_real_held == pytest.approx(starting_held)

        wb = (
            await session.execute(
                select(WalletBalance).where(
                    WalletBalance.tenant_id == tenant.id,
                    WalletBalance.player_id == player.id,
                    WalletBalance.currency == "USD",
                )
            )
        ).scalars().first()
        if wb:
            assert wb.balance_real_available == pytest.approx(starting_wb_available)
            assert wb.balance_real_pending == pytest.approx(starting_wb_pending)

        # There must be no additional ledger event with status "deposit_succeeded"
        txs = (
            await session.execute(
                select(Transaction).where(
                    Transaction.tenant_id == tenant.id,
                    Transaction.player_id == player.id,
                    Transaction.type == "deposit",
                )
            )
        ).scalars().all()

        # Either no tx at all, or only non-succeeded/failed ones without balance deltas
        for tx in txs:
            evs = (
                await session.execute(
                    select(LedgerTransaction).where(
                        LedgerTransaction.player_id == player.id,
                        LedgerTransaction.tx_id == str(tx.id),
                        LedgerTransaction.status == "deposit_succeeded",
                    )
                )
            ).scalars().all()
            assert len(evs) == 0
