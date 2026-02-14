from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from app.repositories.ledger_repo import append_event, apply_balance_delta, LedgerTransaction


@dataclass
class AppendResult:
    event: LedgerTransaction
    created: bool


async def shadow_append_event(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    tx_id: Optional[str],
    type: str,
    direction: str,
    amount: float,
    currency: str,
    status: str,
    idempotency_key: Optional[str] = None,
    provider: Optional[str] = None,
    provider_ref: Optional[str] = None,
    provider_event_id: Optional[str] = None,
) -> Optional[AppendResult]:
    """Shadow wrapper around append_event.

    - Respects settings.ledger_shadow_write
    - Never raises (swallows errors in shadow mode)
    - Returns AppendResult or None if disabled/fails
    """

    if not settings.ledger_shadow_write:
        return None

    try:
        event, created = await append_event(
            session,
            tenant_id=tenant_id,
            player_id=player_id,
            tx_id=tx_id,
            type=type,
            direction=direction,
            amount=amount,
            currency=currency,
            status=status,
            idempotency_key=idempotency_key,
            provider=provider,
            provider_ref=provider_ref,
            provider_event_id=provider_event_id,
            autocommit=True,
        )
        return AppendResult(event=event, created=created)
    except Exception:
        # In shadow mode we deliberately avoid breaking the main flow
        return None


async def shadow_apply_delta(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    currency: str,
    delta_available: float,
    delta_pending: float,
) -> None:
    """Shadow wrapper around apply_balance_delta.

    Only runs when ledger_shadow_write is enabled and never raises.
    """

    if not settings.ledger_shadow_write:
        return

    try:
        await apply_balance_delta(
            session,
            tenant_id=tenant_id,
            player_id=player_id,
            currency=currency,
            delta_available=delta_available,
            delta_pending=delta_pending,
            autocommit=True,
        )
    except Exception:
        return
