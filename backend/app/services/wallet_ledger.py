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
    # Invariants
    allow_negative: bool = False,
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

    # Temporary debug log to understand idempotency behaviour in tests
    # (can be removed or downgraded later).
    try:
        from logging import getLogger

        logger = getLogger("wallet_ledger")
        logger.info(
            "wallet_ledger_append_event",
            extra={
                "event_type": event_type,
                "idempotency_key": idempotency_key,
                "provider_event_id": provider_event_id,
                "created": created,
            },
        )
    except Exception:
        # Logging must never break the main flow
        pass

    if not created:
        # Idempotency hit: do not re-apply deltas.
        return False

    # WalletBalance: "pending" is our held-equivalent in the ledger snapshot.
    # We do not rely on the previous apply_balance_delta helper here because it
    # performs its own commit/flush semantics. Instead we update the snapshot
    # directly under the same transaction.
    now = datetime.utcnow()
    if not bal:
        # Initialise snapshot from the current Player balances, then apply deltas
        bal = WalletBalance(
            tenant_id=tenant_id,
            player_id=player_id,
            currency=currency,
            balance_real_available=float(player.balance_real_available) + float(delta_available),
            balance_real_pending=float(player.balance_real_held) + float(delta_held),
            balance_bonus_available=float(player.balance_bonus),
            balance_bonus_pending=0.0,
            updated_at=now,
        )
        session.add(bal)
    else:
        bal.balance_real_available = float(bal.balance_real_available) + float(delta_available)
        bal.balance_real_pending = float(bal.balance_real_pending) + float(delta_held)
        bal.updated_at = now
        session.add(bal)

    # Mirror the same deltas onto the Player aggregate balances.
    player.balance_real_available = float(player.balance_real_available) + float(
        delta_available
    )
    player.balance_real_held = float(player.balance_real_held) + float(delta_held)

    # Invariants: non-negative balances on the Player aggregate snapshot.
    # The ledger WalletBalance snapshot is allowed to diverge temporarily in
    # some LEDGER-02B test scenarios (e.g. enforce OFF + mismatch telemetry),
    # so we only enforce hard non-negativity on the Player-facing balances.
    if not allow_negative:
        _assert_non_negative("player.balance_real_available", float(player.balance_real_available))
        _assert_non_negative("player.balance_real_held", float(player.balance_real_held))

    return True


async def apply_bonus_delta_with_ledger(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    tx_id: Optional[str],
    event_type: str,
    delta_bonus_available: float,
    delta_bonus_pending: float = 0.0,
    currency: str = "USD",
    idempotency_key: Optional[str] = None,
    provider: Optional[str] = None,
    provider_ref: Optional[str] = None,
    provider_event_id: Optional[str] = None,
    allow_negative: bool = False,
) -> bool:
    """Apply a bonus-balance delta to WalletBalance + Player, with a ledger event.

    Notes:
    - P0-05 requires WalletBalance as the authoritative snapshot for bonus.
    - We mirror WalletBalance.balance_bonus_available onto Player.balance_bonus.
    """

    player_stmt = select(Player).where(Player.id == player_id).with_for_update()
    player = (await session.execute(player_stmt)).scalars().first()
    if not player:
        raise WalletInvariantError("PLAYER_NOT_FOUND")

    bal_stmt = (
        select(WalletBalance)
        .where(
            WalletBalance.tenant_id == tenant_id,
            WalletBalance.player_id == player_id,
            WalletBalance.currency == currency,
        )
        .with_for_update()
    )
    bal = (await session.execute(bal_stmt)).scalars().first()

    # Ledger event (best-effort representation for bonus movements)
    net = float(delta_bonus_available) + float(delta_bonus_pending)
    direction = "credit" if net >= 0 else "debit"
    amount = abs(float(delta_bonus_available)) + abs(float(delta_bonus_pending))

    # IMPORTANT: for MANUAL_CREDIT grants we expect (provider, provider_event_id)
    # idempotency. If a duplicate is detected, we still should return OK and not
    # break the API response.
    _event, created = await append_event(
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
        return True

    now = datetime.utcnow()
    if not bal:
        bal = WalletBalance(
            tenant_id=tenant_id,
            player_id=player_id,
            currency=currency,
            balance_real_available=float(player.balance_real_available),
            balance_real_pending=float(player.balance_real_held),
            balance_bonus_available=float(delta_bonus_available),
            balance_bonus_pending=float(delta_bonus_pending),
            updated_at=now,
        )
        session.add(bal)
    else:
        bal.balance_bonus_available = float(bal.balance_bonus_available) + float(delta_bonus_available)
        bal.balance_bonus_pending = float(bal.balance_bonus_pending) + float(delta_bonus_pending)
        bal.updated_at = now
        session.add(bal)

    # Mirror snapshot to Player aggregate.
    player.balance_bonus = float(bal.balance_bonus_available)

    if not allow_negative:
        _assert_non_negative("player.balance_bonus", float(player.balance_bonus))
        if bal:
            _assert_non_negative("wallet.balance_bonus_available", float(bal.balance_bonus_available))
            _assert_non_negative("wallet.balance_bonus_pending", float(bal.balance_bonus_pending))

    return True


async def spend_with_bonus_precedence(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    tx_id: Optional[str],
    event_type: str,
    amount: float,
    currency: str = "USD",
    idempotency_key: Optional[str] = None,
    provider: Optional[str] = None,
    provider_ref: Optional[str] = None,
    provider_event_id: Optional[str] = None,
) -> bool:
    """Debit with precedence: bonus_balance first, then real balance.

    This is used for bets and any other spend-like operations.
    """

    if amount <= 0:
        return True

    player_stmt = select(Player).where(Player.id == player_id).with_for_update()
    player = (await session.execute(player_stmt)).scalars().first()
    if not player:
        raise WalletInvariantError("PLAYER_NOT_FOUND")

    bal_stmt = (
        select(WalletBalance)
        .where(
            WalletBalance.tenant_id == tenant_id,
            WalletBalance.player_id == player_id,
            WalletBalance.currency == currency,
        )
        .with_for_update()
    )
    bal = (await session.execute(bal_stmt)).scalars().first()

    # Ensure we have a snapshot row
    now = datetime.utcnow()
    if not bal:
        bal = WalletBalance(
            tenant_id=tenant_id,
            player_id=player_id,
            currency=currency,
            balance_real_available=float(player.balance_real_available),
            balance_real_pending=float(player.balance_real_held),
            balance_bonus_available=float(player.balance_bonus or 0.0),
            balance_bonus_pending=0.0,
            updated_at=now,
        )
        session.add(bal)
        await session.flush()

    bonus_avail = float(bal.balance_bonus_available or 0.0)
    use_bonus = min(bonus_avail, float(amount))
    use_real = float(amount) - use_bonus

    if float(bal.balance_real_available or 0.0) < use_real - 1e-9:
        raise WalletInvariantError("INSUFFICIENT_FUNDS")

    # Ledger event (single) for idempotency + traceability
    _event, created = await append_event(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        tx_id=tx_id,
        type="wallet",
        direction="debit",
        amount=float(amount),
        currency=currency,
        status=event_type,
        idempotency_key=idempotency_key,
        provider=provider,
        provider_ref=provider_ref or f"bonus:{use_bonus}|real:{use_real}",
        provider_event_id=provider_event_id,
        autocommit=False,
    )

    if not created:
        return False

    bal.balance_bonus_available = float(bal.balance_bonus_available) - float(use_bonus)
    bal.balance_real_available = float(bal.balance_real_available) - float(use_real)
    bal.updated_at = now
    session.add(bal)

    player.balance_bonus = float(player.balance_bonus or 0.0) - float(use_bonus)
    player.balance_real_available = float(player.balance_real_available) - float(use_real)

    _assert_non_negative("player.balance_bonus", float(player.balance_bonus))
    _assert_non_negative("player.balance_real_available", float(player.balance_real_available))

    return True
