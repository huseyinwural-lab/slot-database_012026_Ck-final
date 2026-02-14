import os
import sys
import asyncio

from sqlmodel import select

sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from app.repositories.ledger_repo import LedgerTransaction
from app.models.reconciliation import ReconciliationFinding
from app.jobs.reconcile_psp import reconcile_mockpsp_vs_ledger
from app.services.psp import get_psp, _reset_psp_singleton_for_tests


async def _count_findings(async_session_factory):
    async with async_session_factory() as session:
        res = await session.execute(select(ReconciliationFinding))
        return len(res.scalars().all())


def test_psp_reconciliation_missing_in_ledger_and_missing_in_psp(async_session_factory):
    async def _run():
        _reset_psp_singleton_for_tests()
        psp = get_psp()

        async with async_session_factory() as session:
            # Seed one ledger event with provider_event_id but no PSP event
            le = LedgerTransaction(
                tenant_id="t-ledger",
                player_id="p-ledger",
                tx_id="tx-ledger",
                type="deposit",
                direction="credit",
                amount=10.0,
                currency="USD",
                status="deposit_captured",
                provider="mockpsp",
                provider_ref="mockpsp:tx-ledger",
                provider_event_id="evt-ledger-only",
            )
            session.add(le)
            await session.commit()

        # Seed one PSP event with no ledger entry
        # Use private API by triggering mock PSP actions
        # (authorize/capture/payout all share store behind export_events).
        await psp.authorize_deposit(
            tx_id="tx-psp-only",
            tenant_id="t-psp",
            player_id="p-psp",
            amount=5.0,
            currency="USD",
            psp_idem_key="tx_tx-psp-only",
        )

        async with async_session_factory() as session:
            await reconcile_mockpsp_vs_ledger(session)

            res = await session.execute(select(ReconciliationFinding))
            findings = res.scalars().all()
            types = {f.finding_type for f in findings}
            assert "missing_in_ledger" in types
            assert "missing_in_psp" in types

    asyncio.run(_run())


def test_psp_reconciliation_idempotent(async_session_factory):
    async def _run():
        _reset_psp_singleton_for_tests()
        psp = get_psp()

        async with async_session_factory() as session:
            # Seed one ledger event and one PSP event so that both sides have data
            le = LedgerTransaction(
                tenant_id="t-ledger2",
                player_id="p-ledger2",
                tx_id="tx-ledger2",
                type="deposit",
                direction="credit",
                amount=20.0,
                currency="USD",
                status="deposit_captured",
                provider="mockpsp",
                provider_ref="mockpsp:tx-ledger2",
                provider_event_id="evt-ledger2",
            )
            session.add(le)
            await session.commit()

        await psp.capture_deposit(
            tx_id="tx-psp2",
            tenant_id="t-psp2",
            player_id="p-psp2",
            amount=15.0,
            currency="USD",
            psp_idem_key="tx_tx-psp2",
        )

        # First run
        async with async_session_factory() as session:
            await reconcile_mockpsp_vs_ledger(session)

        first_count = await _count_findings(async_session_factory)

        # Second run should not change count in an ideal idempotent implementation,
        # but current MVP does not enforce DB-level uniqueness. This test ensures
        # at least that growth is controlled for future enhancement.
        async with async_session_factory() as session:
            await reconcile_mockpsp_vs_ledger(session)

        second_count = await _count_findings(async_session_factory)
        assert second_count == first_count

    asyncio.run(_run())
