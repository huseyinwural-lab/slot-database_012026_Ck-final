from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date as date_cls
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sql_models import Transaction, PayoutAttempt
from app.repositories.ledger_repo import LedgerTransaction


@dataclass
class FindingDTO:
    tenant_id: str
    tx_id: str
    finding_code: str
    severity: str
    detected_at: datetime
    details: Dict[str, Any]


def _day_window_utc(d: date_cls) -> tuple[datetime, datetime]:
    """Return [day_start, day_end) in UTC for given date."""
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


async def compute_daily_findings(
    session: AsyncSession,
    *,
    day: date_cls,
    tenant_id: Optional[str] = None,
) -> List[FindingDTO]:
    """Compute wallet-ledger related money-path invariants for a given UTC day.

    This is *compute-only*; persistence is handled by the reconciliation run
    service. All queries are scoped to the provided day window.
    """

    start, end = _day_window_utc(day)
    findings: List[FindingDTO] = []

    # Base transaction query for withdrawals
    tx_base = select(Transaction).where(
        Transaction.type == "withdrawal",
        Transaction.created_at >= start,
        Transaction.created_at < end,
    )
    if tenant_id:
        tx_base = tx_base.where(Transaction.tenant_id == tenant_id)

    tx_rows = (await session.execute(tx_base)).scalars().all()

    # Preload ledger events for these tx_ids
    tx_ids = [str(tx.id) for tx in tx_rows]
    if tx_ids:
        led_stmt = select(LedgerTransaction).where(LedgerTransaction.tx_id.in_(tx_ids))
        ledgers = (await session.execute(led_stmt)).scalars().all()
    else:
        ledgers = []

    ledger_by_tx: Dict[str, List[LedgerTransaction]] = {}
    for ev in ledgers:
        ledger_by_tx.setdefault(ev.tx_id, []).append(ev)

    # Withdrawal invariants
    for tx in tx_rows:
        key = str(tx.id)
        tenant = tx.tenant_id
        events = ledger_by_tx.get(key, [])
        withdraw_paid_events = [e for e in events if e.status == "withdraw_paid"]

        detected_at = datetime.now(timezone.utc)

        if tx.state == "paid":
            if len(withdraw_paid_events) == 0:
                findings.append(
                    FindingDTO(
                        tenant_id=tenant,
                        tx_id=key,
                        finding_code="LEDGER_MISSING_WITHDRAW_PAID",
                        severity="CRITICAL",
                        detected_at=detected_at,
                        details={"state": tx.state},
                    )
                )
            elif len(withdraw_paid_events) > 1:
                findings.append(
                    FindingDTO(
                        tenant_id=tenant,
                        tx_id=key,
                        finding_code="LEDGER_DUPLICATE_WITHDRAW_PAID",
                        severity="CRITICAL",
                        detected_at=detected_at,
                        details={"count": len(withdraw_paid_events)},
                    )
                )
        else:
            if len(withdraw_paid_events) > 0:
                findings.append(
                    FindingDTO(
                        tenant_id=tenant,
                        tx_id=key,
                        finding_code="LEDGER_PRESENT_BUT_TX_NOT_PAID",
                        severity="CRITICAL",
                        detected_at=detected_at,
                        details={"state": tx.state, "count": len(withdraw_paid_events)},
                    )
                )

    # PayoutAttempt invariants for withdrawals
    if tx_ids:
        pa_stmt = select(PayoutAttempt).where(PayoutAttempt.withdraw_tx_id.in_(tx_ids))
        attempts = (await session.execute(pa_stmt)).scalars().all()
    else:
        attempts = []

    attempts_by_tx: Dict[str, List[PayoutAttempt]] = {}
    dup_provider_events: Dict[tuple[str, str], int] = {}

    for pa in attempts:
        attempts_by_tx.setdefault(pa.withdraw_tx_id, []).append(pa)
        if pa.provider and pa.provider_event_id:
            key_pe = (pa.provider, pa.provider_event_id)
            dup_provider_events[key_pe] = dup_provider_events.get(key_pe, 0) + 1

    # Missing attempts for paid withdrawals
    for tx in tx_rows:
        if tx.state == "paid":
            tx_attempts = attempts_by_tx.get(str(tx.id), [])
            if not tx_attempts:
                findings.append(
                    FindingDTO(
                        tenant_id=tx.tenant_id,
                        tx_id=str(tx.id),
                        finding_code="PAYOUT_ATTEMPT_MISSING_FOR_PAID",
                        severity="HIGH",
                        detected_at=datetime.now(timezone.utc),
                        details={},
                    )
                )

    # Duplicate provider_event_id attempts
    for (provider, provider_event_id), count in dup_provider_events.items():
        if count > 1:
            findings.append(
                FindingDTO(
                    tenant_id="*",  # can be refined if needed
                    tx_id="*",
                    finding_code="PAYOUT_ATTEMPT_DUPLICATE_PROVIDER_EVENT",
                    severity="HIGH",
                    detected_at=datetime.now(timezone.utc),
                    details={"provider": provider, "provider_event_id": provider_event_id, "count": count},
                )
            )

    # Deposit invariants (minimal): completed deposit without deposit_succeeded ledger
    dep_stmt = select(Transaction).where(
        Transaction.type == "deposit",
        Transaction.state == "completed",
        Transaction.created_at >= start,
        Transaction.created_at < end,
    )
    if tenant_id:
        dep_stmt = dep_stmt.where(Transaction.tenant_id == tenant_id)

    deposits = (await session.execute(dep_stmt)).scalars().all()
    dep_ids = [str(tx.id) for tx in deposits]
    if dep_ids:
        dep_led_stmt = select(LedgerTransaction).where(LedgerTransaction.tx_id.in_(dep_ids))
        dep_ledgers = (await session.execute(dep_led_stmt)).scalars().all()
    else:
        dep_ledgers = []

    dep_ledger_by_tx: Dict[str, List[LedgerTransaction]] = {}
    for ev in dep_ledgers:
        dep_ledger_by_tx.setdefault(ev.tx_id, []).append(ev)

    for tx in deposits:
        evs = dep_ledger_by_tx.get(str(tx.id), [])
        deposit_succeeded = [e for e in evs if e.status == "deposit_succeeded"]
        if len(deposit_succeeded) == 0:
            findings.append(
                FindingDTO(
                    tenant_id=tx.tenant_id,
                    tx_id=str(tx.id),
                    finding_code="LEDGER_MISSING_DEPOSIT_CAPTURED",
                    severity="MEDIUM",
                    detected_at=datetime.now(timezone.utc),
                    details={},
                )
            )

    return findings
