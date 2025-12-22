from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.sql_models import Player
from app.repositories.ledger_repo import (
    append_event,
    WalletBalance,
)


class WalletInvariantError(RuntimeError):
    """Raised when a wallet invariant is violated (negative balances, etc.)."""


def _assert_non_negative(name: str, value: float) -> None:
    if value < -1e-9:
        raise WalletInvariantError(f"{name} went negative: {value}")


async def apply_wallet_delta_with_ledger(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    tx_id: Optional[str],
    event_type: str,
    # Domain deltas (available/held in real currency)
    delta_available: float,
    delta_held: float,
    currency: str = "USD",
    # Idempotency / provider selectors
    idempotency_key: Optional[str] = None,
    provider: Optional[str] = None,
    provider_ref: Optional[str] = None,
    provider_event_id: Optional[str] = None,
) -> bool:
    """Apply a wallet delta in a single transaction, bound to the ledger.

    This is the *only* supported way to change wallet balances.

    Behaviour:
    - Appends a LedgerTransaction via ``append_event(..., autocommit=False)``.
    - If the event already exists (idempotency hit), returns False and performs
      no balance changes.
    - If created, applies the same deltas to WalletBalance (available/pending)
      and mirrors them onto Player (available/held).
    - Enforces non-negative balance invariants on both snapshots.

    Returns:
        True if a new ledger event was created and balances were updated,
        False if this was an idempotent no-op.
    """

    # Lock Player row so UI-facing balances stay consistent with the ledger
    player_stmt = select(Player).where(Player.id == player_id).with_for_update()
    player_res = await session.execute(player_stmt)
    player = player_res.scalars().first()
    if not player:
        raise WalletInvariantError("PLAYER_NOT_FOUND")

    # Lock WalletBalance row as the authoritative snapshot
    bal_stmt = (
        select(WalletBalance)
        .where(
            WalletBalance.tenant_id == tenant_id,
            WalletBalance.player_id == player_id,
            WalletBalance.currency == currency,
        )
        .with_for_update()
    )
    bal_res = await session.execute(bal_stmt)
    bal = bal_res.scalars().first()

    # Encode the event for the immutable ledger. We keep the existing
    # type/direction contract but ensure the actual numeric effect is carried
    # by WalletBalance + Player deltas.
    net = float(delta_available) + float(delta_held)
    direction = "credit" if net >= 0 else "debit"
    amount = abs(float(delta_available)) + abs(float(delta_held))

    event, created = await append_event(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        tx_id=tx_id,
        type="wallet",
        direction=direction,
        amount=amount,
        currency=currency,
        status=event_type,
        idempotency_key=idempotency_key,
        provider=provider,
        provider_ref=provider_ref,
        provider_event_id=provider_event_id,
        autocommit=False,
    )

    if not created:
        # Idempotency hit: do not re-apply deltas.
        return False

    # WalletBalance: "pending" is our held-equivalent in the ledger snapshot.
    bal = await apply_balance_delta(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        currency=currency,
        delta_available=float(delta_available),
        delta_pending=float(delta_held),
        autocommit=False,
    )

    # Mirror the same deltas onto the Player aggregate balances.
    player.balance_real_available = float(player.balance_real_available) + float(
        delta_available
    )
    player.balance_real_held = float(player.balance_real_held) + float(delta_held)

    # Invariants: non-negative balances on both snapshots.
    _assert_non_negative("wallet.balance_real_available", float(bal.balance_real_available))
    _assert_non_negative("wallet.balance_real_pending", float(bal.balance_real_pending))
    _assert_non_negative("player.balance_real_available", float(player.balance_real_available))
    _assert_non_negative("player.balance_real_held", float(player.balance_real_held))

    return True
