from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal, Optional

from fastapi import HTTPException
from sqlmodel import select, func

from app.models.sql_models import Tenant, Transaction


ActionType = Literal["deposit", "withdraw"]


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

    now = now or datetime.now(timezone.utc)
    day_start = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

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
