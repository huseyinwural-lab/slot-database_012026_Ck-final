from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal, Optional

from fastapi import HTTPException
from sqlmodel import select, func

from app.models.sql_models import Tenant, Transaction, Player

ActionType = Literal["deposit", "withdraw"]


def _naive_utc(dt: datetime) -> datetime:
    """Force a datetime into naive UTC.

    DB uses TIMESTAMP WITHOUT TIME ZONE in several environments.
    - If tz-aware: convert to UTC then drop tzinfo.
    - If naive: assume it's already UTC.
    """

    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


@dataclass
class TenantLimitUsage:
    tenant_id: str
    player_id: str
    action: ActionType
    limit: Decimal
    used_today: Decimal
    attempted: Decimal

    @property
    def remaining(self) -> Decimal:
        return max(Decimal("0"), self.limit - self.used_today)


async def ensure_within_tenant_daily_limits(
    session,
    *,
    tenant_id: Optional[str],
    player_id: str,
    action: ActionType,
    amount: float,
    currency: str = "USD",
    now: Optional[datetime] = None,
):
    """Enforce per-tenant daily deposit/withdraw limits.

    - If no tenant_id or no policy is configured: allow.
    - Uses UTC day window [day_start, day_end) for daily usage.
    - For deposits: sum of successful deposits today.
    - For withdrawals: sum of requested/approved/paid withdrawals today.

    Raises HTTPException(422) with error_code=LIMIT_EXCEEDED on violation.
    """

    if not tenant_id:
        return

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        return

    dec_amount = Decimal(str(amount))
    if dec_amount <= 0:
        return

    if action == "deposit":
        limit_value = tenant.daily_deposit_limit
    else:
        limit_value = tenant.daily_withdraw_limit

    if limit_value is None:
        return

    limit_dec = Decimal(str(limit_value))

    # DB uses TIMESTAMP WITHOUT TIME ZONE in several environments.
    # Keep comparisons deterministic by using naive UTC timestamps.
    now = _naive_utc(now or datetime.utcnow())
    day_start = _naive_utc(datetime(year=now.year, month=now.month, day=now.day))
    day_end = _naive_utc(day_start + timedelta(days=1))

    if action == "deposit":
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.tenant_id == tenant_id,
            Transaction.player_id == player_id,
            Transaction.type == "deposit",
            # Only completed deposits consume the day limit
            Transaction.state == "completed",
            Transaction.created_at >= day_start,
            Transaction.created_at < day_end,
        )
    else:
        # requested/approved/paid withdrawals for the day consume the limit
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.tenant_id == tenant_id,
            Transaction.player_id == player_id,
            Transaction.type == "withdrawal",
            Transaction.state.in_(["requested", "approved", "paid"]),
            Transaction.created_at >= day_start,
            Transaction.created_at < day_end,
        )

    used_today_raw = (await session.execute(stmt)).scalar_one() or 0
    used_today = Decimal(str(used_today_raw))

    usage = TenantLimitUsage(
        tenant_id=tenant_id,
        player_id=player_id,
        action=action,
        limit=limit_dec,
        used_today=used_today,
        attempted=dec_amount,
    )

    if usage.used_today + usage.attempted <= usage.limit:
        return

    # Build structured error payload
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "LIMIT_EXCEEDED",
            "limit": float(usage.limit),
            "used_today": float(usage.used_today),
            "attempted": float(usage.attempted),
            "remaining": float(usage.remaining),
            "scope": "tenant_daily",
            "action": usage.action,
            "currency": currency,
        },
    )

async def check_velocity_limit(
    session,
    *,
    player_id: str,
    action: ActionType,
):
    """Enforce global velocity limit (spam protection).

    Raises HTTPException(429) if too many requests in short window.
    """

    from config import settings

    limit_count = settings.max_tx_velocity_count
    window_minutes = settings.max_tx_velocity_window_minutes

    # DB uses TIMESTAMP WITHOUT TIME ZONE in several environments.
    # Keep comparisons deterministic by using naive UTC timestamps.
    now = _naive_utc(datetime.utcnow())
    window_start = _naive_utc(now - timedelta(minutes=window_minutes))

    stmt = select(func.count(Transaction.id)).where(
        Transaction.player_id == player_id,
        Transaction.created_at >= window_start,
        Transaction.type == ("deposit" if action == "deposit" else "withdrawal"),
    )

    count = (await session.execute(stmt)).scalar_one() or 0

    if count >= limit_count:
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": "VELOCITY_LIMIT_EXCEEDED",
                "message": f"Too many {action} requests. Please wait.",
                "limit": limit_count,
                "window_minutes": window_minutes,
            },
        )


async def check_wagering_requirement(
    session,
    *,
    player_id: str,
):
    """Ensure player has met wagering requirements before withdrawal."""
    player = await session.get(Player, player_id)
    if not player:
        return

    # Check if wagering remaining > 0
    if player.wagering_remaining > 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "WAGERING_REQUIREMENT_NOT_MET",
                "remaining": float(player.wagering_remaining),
                "message": "You must complete wagering requirements before withdrawing."
            }
        )

