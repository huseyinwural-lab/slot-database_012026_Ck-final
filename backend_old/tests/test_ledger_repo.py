import os
import sys
import asyncio

import pytest
from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from app.repositories.ledger_repo import (
    LedgerTransaction,
    append_event,
    get_balance,
    apply_balance_delta,
)
from tests.conftest import _create_tenant, _create_player


@pytest.mark.usefixtures("client")
def test_append_event_idempotency_client(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id)

            e1, created1 = await append_event(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-1",
                type="deposit",
                direction="credit",
                amount=10,
                currency="USD",
                status="deposit_captured",
                idempotency_key="idem-1",
            )

            e2, created2 = await append_event(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-1",
                type="deposit",
                direction="credit",
                amount=10,
                currency="USD",
                status="deposit_captured",
                idempotency_key="idem-1",
            )

            assert e1.id == e2.id

            stmt = select(LedgerTransaction).where(LedgerTransaction.tenant_id == tenant.id)
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 1

    asyncio.run(_run())


@pytest.mark.usefixtures("client")
def test_append_event_idempotency_provider(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id)

            e1, created1 = await append_event(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-2",
                type="deposit",
                direction="credit",
                amount=20,
                currency="USD",
                status="deposit_captured",
                idempotency_key=None,
                provider="mockpsp",
                provider_ref="pay_123",
                provider_event_id="evt_1",
            )

            e2, created2 = await append_event(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-2",
                type="deposit",
                direction="credit",
                amount=20,
                currency="USD",
                status="deposit_captured",
                idempotency_key=None,
                provider="mockpsp",
                provider_ref="pay_123",
                provider_event_id="evt_1",
            )

            assert e1.id == e2.id

            stmt = select(LedgerTransaction).where(LedgerTransaction.provider_event_id == "evt_1")
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 1

    asyncio.run(_run())


@pytest.mark.usefixtures("client")
def test_balance_snapshot_create_and_update(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id)

            # Initial zero read
            bal0 = await get_balance(session, tenant_id=tenant.id, player_id=player.id, currency="USD")
            assert bal0.balance_real_available == 0
            assert bal0.balance_real_pending == 0

            # Apply first delta (create row)
            bal1 = await apply_balance_delta(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                currency="USD",
                delta_available=100,
                delta_pending=0,
            )
            assert bal1.balance_real_available == 100
            assert bal1.balance_real_pending == 0

            # Apply second delta (update row)
            bal2 = await apply_balance_delta(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                currency="USD",
                delta_available=-30,
                delta_pending=10,
            )
            assert bal2.balance_real_available == 70
            assert bal2.balance_real_pending == 10

    asyncio.run(_run())


@pytest.mark.usefixtures("client")
def test_ledger_event_indexable_by_tx_id(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant.id)

            await append_event(
                session,
                tenant_id=tenant.id,
                player_id=player.id,
                tx_id="tx-ledger-1",
                type="withdraw",
                direction="debit",
                amount=15,
                currency="USD",
                status="withdraw_requested",
                idempotency_key="idem-ledger-1",
            )

            stmt = select(LedgerTransaction).where(LedgerTransaction.tx_id == "tx-ledger-1")
            rows = (await session.execute(stmt)).scalars().all()
            assert len(rows) == 1

    asyncio.run(_run())
