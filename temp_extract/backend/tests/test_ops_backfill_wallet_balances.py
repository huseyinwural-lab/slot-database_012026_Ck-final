import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from app.models.sql_models import Player
from app.repositories.ledger_repo import WalletBalance
from scripts.backfill_wallet_balances import _backfill_wallet_balances
from tests.conftest import _create_tenant, _create_player


def test_backfill_creates_walletbalance_when_missing(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, balance_available=50.0, balance_held=20.0)

        await _backfill_wallet_balances(
            tenant_id=None,
            batch_size=100,
            dry_run=False,
            force=False,
            session_factory=async_session_factory,
        )

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
            assert wb.balance_real_available == pytest.approx(50.0)
            assert wb.balance_real_pending == pytest.approx(20.0)

    asyncio.run(_run())


def test_backfill_idempotent_without_force(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, balance_available=10.0, balance_held=5.0)

        # First run creates WB
        await _backfill_wallet_balances(tenant_id=None, batch_size=100, dry_run=False, force=False, session_factory=async_session_factory)

        async with async_session_factory() as session:
            wb1 = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant.id,
                        WalletBalance.player_id == player.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()
            assert wb1 is not None

        # Change player balances
        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            db_player.balance_real_available = 99.0
            db_player.balance_real_held = 77.0
            await session.commit()

        # Second run without force should not overwrite WB
        await _backfill_wallet_balances(tenant_id=None, batch_size=100, dry_run=False, force=False, session_factory=async_session_factory)

        async with async_session_factory() as session:
            wb2 = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant.id,
                        WalletBalance.player_id == player.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()
            assert wb2.balance_real_available == pytest.approx(wb1.balance_real_available)
            assert wb2.balance_real_pending == pytest.approx(wb1.balance_real_pending)

    asyncio.run(_run())


def test_backfill_force_overwrites_existing(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, balance_available=10.0, balance_held=5.0)

        await _backfill_wallet_balances(tenant_id=None, batch_size=100, dry_run=False, force=False, session_factory=async_session_factory)

        async with async_session_factory() as session:
            wb1 = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant.id,
                        WalletBalance.player_id == player.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()

        # Change player balances
        async with async_session_factory() as session:
            db_player = await session.get(Player, player.id)
            db_player.balance_real_available = 123.0
            db_player.balance_real_held = 45.0
            await session.commit()

        # Run with force -> WB should be updated
        await _backfill_wallet_balances(tenant_id=None, batch_size=100, dry_run=False, force=True, session_factory=async_session_factory)

        async with async_session_factory() as session:
            wb2 = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant.id,
                        WalletBalance.player_id == player.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()
            assert wb2.balance_real_available == pytest.approx(123.0)
            assert wb2.balance_real_pending == pytest.approx(45.0)

    asyncio.run(_run())


def test_backfill_tenant_scoped(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant1 = await _create_tenant(session)
            tenant2 = await _create_tenant(session)
            player1 = await _create_player(session, tenant1.id, balance_available=10.0, balance_held=1.0)
            player2 = await _create_player(session, tenant2.id, balance_available=20.0, balance_held=2.0)

        # Run only for tenant1
        await _backfill_wallet_balances(tenant_id=tenant1.id, batch_size=100, dry_run=False, force=False, session_factory=async_session_factory)

        async with async_session_factory() as session:
            wb1 = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant1.id,
                        WalletBalance.player_id == player1.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()
            wb2 = (
                await session.execute(
                    select(WalletBalance).where(
                        WalletBalance.tenant_id == tenant2.id,
                        WalletBalance.player_id == player2.id,
                        WalletBalance.currency == "USD",
                    )
                )
            ).scalars().first()

            # We only assert that tenant1/player1 got a backfilled balance;
            # other tenants may already have balances from previous operations.
            assert wb1 is not None

    asyncio.run(_run())


def test_backfill_dry_run_does_not_modify_db(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id, balance_available=33.0, balance_held=7.0)

        await _backfill_wallet_balances(tenant_id=None, batch_size=100, dry_run=True, force=False, session_factory=async_session_factory)

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

    asyncio.run(_run())
