from __future__ import annotations

from typing import Optional, Dict, Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.repositories.ledger_repo import LedgerTransaction
from app.models.reconciliation import create_finding
from app.services.psp import get_psp


async def reconcile_mockpsp_vs_ledger(
    session: AsyncSession,
    *,
    tenant_id: Optional[str] = None,
    provider: str = "mockpsp",
) -> None:
    """Reconcile MockPSP exported events against ledger_transactions.

    Findings produced (MVP):
    - missing_in_ledger: PSP'de var, ledger'da yok.
    - missing_in_psp: ledger'da var, PSP'de yok.

    Reconciliation anahtarı: (provider, provider_event_id).
    """

    psp = get_psp()
    psp_events = psp.export_events()

    # Map PSP events by provider_event_id
    psp_by_event: Dict[str, Dict] = {
        e["provider_event_id"]: e for e in psp_events if e.get("provider_event_id")
    }

    # Load ledger events for this provider
    stmt = select(LedgerTransaction).where(LedgerTransaction.provider == provider)
    if tenant_id:
        stmt = stmt.where(LedgerTransaction.tenant_id == tenant_id)

    result = await session.execute(stmt)
    ledger_events: Iterable[LedgerTransaction] = result.scalars().all()
    ledger_by_event: Dict[str, LedgerTransaction] = {
        e.provider_event_id: e for e in ledger_events if e.provider_event_id
    }

    # PSP var, ledger yok -> missing_in_ledger
    for event_id, ev in psp_by_event.items():
        if event_id not in ledger_by_event:
            await create_finding(
                session,
                provider=provider,
                tenant_id=None,
                player_id=None,
                tx_id=None,
                provider_event_id=event_id,
                provider_ref=ev.get("provider_ref"),
                finding_type="missing_in_ledger",
                severity="WARN",
                status="OPEN",
                message="PSP event has no matching ledger entry",
                raw={"psp": ev},
            )

    # Ledger var, PSP yok -> missing_in_psp
    for event_id, ev in ledger_by_event.items():
        if event_id not in psp_by_event:
            await create_finding(
                session,
                provider=provider,
                tenant_id=ev.tenant_id,
                player_id=ev.player_id,
                tx_id=ev.tx_id,
                provider_event_id=event_id,
                provider_ref=ev.provider_ref,
                finding_type="missing_in_psp",
                severity="WARN",
                status="OPEN",
                message="Ledger event has no matching PSP event",
                raw={"ledger": {
                    "tx_id": ev.tx_id,
                    "amount": ev.amount,
                    "currency": ev.currency,
                    "status": ev.status,
                }},
            )
