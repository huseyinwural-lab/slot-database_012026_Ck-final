from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field, select
from typing import Tuple

import uuid


class LedgerTransaction(SQLModel, table=True):
    """Immutable ledger event log (append-only).

    This is introduced alongside the existing Transaction model and does not
    replace it yet. It will become the canonical financial event store in
    later phases (LEDGER-02+).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    tx_id: Optional[str] = Field(default=None, index=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(index=True)

    type: str  # deposit|withdraw|adjustment|fee|reversal
    direction: str  # credit|debit

    amount: float
    currency: str = "USD"

    status: str  # deposit_initiated, withdraw_requested, etc.

    # Idempotency keys
    idempotency_key: Optional[str] = Field(default=None, index=True)

    # Provider linkage (optional for PSP integration)
    provider: Optional[str] = Field(default=None, index=True)
    provider_ref: Optional[str] = Field(default=None, index=True)
    provider_event_id: Optional[str] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow(), index=True)


class WalletBalance(SQLModel, table=True):
    """Materialized wallet snapshot per (tenant, player, currency)."""

    tenant_id: str = Field(primary_key=True)
    player_id: str = Field(primary_key=True)
    currency: str = Field(primary_key=True, default="USD")

    balance_real_available: float = 0.0
    balance_real_pending: float = 0.0

    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow(), index=True)


async def append_event(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    tx_id: Optional[str],
    type: str,
    direction: str,
    amount: float,
    currency: str = "USD",
    status: str,
    idempotency_key: Optional[str] = None,
    provider: Optional[str] = None,
    provider_ref: Optional[str] = None,
    provider_event_id: Optional[str] = None,
) -> Tuple[LedgerTransaction, bool]:
    """Append a ledger event, enforcing idempotency.

    Returns a tuple (event, created):
    - created = True if a new row was inserted
    - created = False if an existing row was reused (idempotency hit)

    Idempotency rules (LEDGER-01):
    - (tenant_id, player_id, type, idempotency_key) is unique when idempotency_key is not null
    - (provider, provider_event_id) is unique when provider_event_id is not null
    """

    existing: Optional[LedgerTransaction] = None

    # Fast path: look for existing event by provider_event_id or idempotency_key
    if provider and provider_event_id:
        stmt = select(LedgerTransaction).where(
            LedgerTransaction.provider == provider,
            LedgerTransaction.provider_event_id == provider_event_id,
        )
        res = await session.execute(stmt)
        existing = res.scalars().first()
    elif idempotency_key:
        stmt = select(LedgerTransaction).where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.player_id == player_id,
            LedgerTransaction.type == type,
            LedgerTransaction.idempotency_key == idempotency_key,
        )
        res = await session.execute(stmt)
        existing = res.scalars().first()

    if existing:
        return existing, False

    # No existing event found; try to insert
    event = LedgerTransaction(
        tx_id=tx_id,
        tenant_id=tenant_id,
        player_id=player_id,
        type=type,
        direction=direction,
        amount=amount,
        currency=currency,
        status=status,
        idempotency_key=idempotency_key,
        provider=provider,
        provider_ref=provider_ref,
        provider_event_id=provider_event_id,
    )

    session.add(event)

    try:
        await session.commit()
        await session.refresh(event)
        return event, True
    except IntegrityError:
        await session.rollback()

        # Try to load the existing event again by the same keys
        if provider and provider_event_id:
            stmt = select(LedgerTransaction).where(
                LedgerTransaction.provider == provider,
                LedgerTransaction.provider_event_id == provider_event_id,
            )
        elif idempotency_key:
            stmt = select(LedgerTransaction).where(
                LedgerTransaction.tenant_id == tenant_id,
                LedgerTransaction.player_id == player_id,
                LedgerTransaction.type == type,
                LedgerTransaction.idempotency_key == idempotency_key,
            )
        else:
            # No idempotency selector available; bubble up
            raise

        res = await session.execute(stmt)
        existing2 = res.scalars().first()
        if not existing2:
            # If we still cannot find, there is a real consistency issue
            raise

        return existing2, False


async def get_balance(
    session: AsyncSession, *, tenant_id: str, player_id: str, currency: str = "USD"
) -> WalletBalance:
    """Return current wallet snapshot; if none exists, return a zeroed one (not persisted)."""

    stmt = select(WalletBalance).where(
        WalletBalance.tenant_id == tenant_id,
        WalletBalance.player_id == player_id,
        WalletBalance.currency == currency,
    )
    res = await session.execute(stmt)
    bal = res.scalars().first()
    if bal:
        return bal

    # Non-persisted zero snapshot
    return WalletBalance(
        tenant_id=tenant_id,
        player_id=player_id,
        currency=currency,
        balance_real_available=0.0,
        balance_real_pending=0.0,
        updated_at=datetime.utcnow(),
    )


async def apply_balance_delta(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    currency: str,
    delta_available: float = 0.0,
    delta_pending: float = 0.0,
) -> WalletBalance:
    """Apply deltas to the wallet snapshot, creating the row if needed.

    This is intentionally simple for LEDGER-01. More strict invariants (e.g.
    preventing negative balances) will be added in LEDGER-02.
    """

    stmt = select(WalletBalance).where(
        WalletBalance.tenant_id == tenant_id,
        WalletBalance.player_id == player_id,
        WalletBalance.currency == currency,
    )
    res = await session.execute(stmt)
    bal = res.scalars().first()

    now = datetime.utcnow()

    if not bal:
        bal = WalletBalance(
            tenant_id=tenant_id,
            player_id=player_id,
            currency=currency,
            balance_real_available=delta_available,
            balance_real_pending=delta_pending,
            updated_at=now,
        )
        session.add(bal)
    else:
        bal.balance_real_available += delta_available
        bal.balance_real_pending += delta_pending
        bal.updated_at = now
        session.add(bal)

    await session.commit()
    await session.refresh(bal)
    return bal
