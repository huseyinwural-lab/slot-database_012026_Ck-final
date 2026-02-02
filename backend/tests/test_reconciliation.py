import os
import sys
from datetime import datetime, timezone, date as date_cls

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.sql_models import Transaction  # noqa: E402
from app.services.reconciliation import compute_daily_findings  # noqa: E402


@pytest.mark.asyncio
async def test_paid_tx_missing_withdraw_paid_finding(client, admin_token, async_session_factory):
    # Seed one paid withdrawal without any ledger events
    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)
        tx = Transaction(
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            status="completed",
            state="paid",
            amount=100.0,
            currency="USD",
            created_at=now,
        )
        session.add(tx)
        await session.commit()

        findings = await compute_daily_findings(session, day=date_cls(now.year, now.month, now.day))

    assert any(f.finding_code == "LEDGER_MISSING_WITHDRAW_PAID" and f.tx_id == str(tx.id) for f in findings)


@pytest.mark.asyncio
async def test_duplicate_withdraw_paid_finding(client, admin_token, async_session_factory):
    # Seed one paid withdrawal with two withdraw_paid ledger events
    from app.repositories.ledger_repo import LedgerTransaction

    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)
        tx = Transaction(
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            status="completed",
            state="paid",
            amount=50.0,
            currency="USD",
            created_at=now,
        )
        session.add(tx)
        await session.commit()

        ev1 = LedgerTransaction(
            tx_id=str(tx.id),
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            direction="debit",
            status="withdraw_paid",
            amount=50.0,
            currency="USD",
            created_at=now,
        )
        ev2 = LedgerTransaction(
            tx_id=str(tx.id),
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            direction="debit",
            status="withdraw_paid",
            amount=50.0,
            currency="USD",
            created_at=now,
        )
        session.add(ev1)
        session.add(ev2)
        await session.commit()

        findings = await compute_daily_findings(session, day=date_cls(now.year, now.month, now.day))

    assert any(f.finding_code == "LEDGER_DUPLICATE_WITHDRAW_PAID" and f.tx_id == str(tx.id) for f in findings)


@pytest.mark.asyncio
async def test_ledger_present_but_tx_not_paid(client, admin_token, async_session_factory):
    from app.repositories.ledger_repo import LedgerTransaction

    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)
        tx = Transaction(
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            status="completed",
            state="payout_failed",
            amount=75.0,
            currency="USD",
            created_at=now,
        )
        session.add(tx)
        await session.commit()

        ev = LedgerTransaction(
            tx_id=str(tx.id),
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            direction="debit",
            status="withdraw_paid",
            amount=75.0,
            currency="USD",
            created_at=now,
        )
        session.add(ev)
        await session.commit()

        findings = await compute_daily_findings(session, day=date_cls(now.year, now.month, now.day))

    assert any(f.finding_code == "LEDGER_PRESENT_BUT_TX_NOT_PAID" and f.tx_id == str(tx.id) for f in findings)


@pytest.mark.asyncio
async def test_duplicate_provider_event_attempt_finding(client, admin_token, async_session_factory):
    from app.models.sql_models import PayoutAttempt

    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)
        tx = Transaction(
            tenant_id="tenant1",
            player_id="player1",
            type="withdrawal",
            status="completed",
            state="payout_pending",
            amount=20.0,
            currency="USD",
            created_at=now,
        )
        session.add(tx)
        await session.commit()

        pa1 = PayoutAttempt(
            withdraw_tx_id=str(tx.id),
            tenant_id="tenant1",
            provider="mockpsp",
            provider_event_id="evt_1",
            idempotency_key="idem_1",
            status="succeeded",
        )
        pa2 = PayoutAttempt(
            withdraw_tx_id=str(tx.id),
            tenant_id="tenant1",
            provider="mockpsp",
            provider_event_id="evt_1",
            idempotency_key="idem_2",
            status="succeeded",
        )
        session.add(pa1)
        session.add(pa2)
        await session.commit()

        findings = await compute_daily_findings(session, day=date_cls(now.year, now.month, now.day))

    assert any(
        f.finding_code == "PAYOUT_ATTEMPT_DUPLICATE_PROVIDER_EVENT" and f.details.get("provider_event_id") == "evt_1"
        for f in findings
    )
