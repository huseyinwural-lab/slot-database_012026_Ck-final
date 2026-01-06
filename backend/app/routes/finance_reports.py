from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/finance", tags=["finance_reports"])


def _to_float(v: Any) -> float:
    try:
        return float(v or 0)
    except Exception:
        return 0.0


@router.get("/reports")
async def get_finance_reports(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    currency: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """P0 Finance reports endpoint.

    Frontend contract (Finance.jsx) expects fields like:
      ggr, ngr, total_deposit, total_withdrawal, provider_breakdown, daily_stats, etc.

    Strategy:
      - Aggregate from Transaction rows when available.
      - Otherwise return deterministic zeros so the UI never breaks.
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Transaction).where(Transaction.tenant_id == tenant_id)

    # Optional date filters (created_at)
    if start_date:
        try:
            # Accept YYYY-MM-DD or ISO datetime
            sd = datetime.fromisoformat(start_date)
            if sd.tzinfo is None:
                sd = sd.replace(tzinfo=timezone.utc)
            stmt = stmt.where(Transaction.created_at >= sd)
        except Exception:
            pass

    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            if ed.tzinfo is None:
                ed = ed.replace(tzinfo=timezone.utc)
            stmt = stmt.where(Transaction.created_at <= ed)
        except Exception:
            pass

    if currency and currency != "all":
        stmt = stmt.where(Transaction.currency == currency)

    rows = (await session.execute(stmt)).scalars().all()

    total_deposit = 0.0
    total_withdrawal = 0.0
    provider_breakdown: Dict[str, float] = {}
    buckets: Dict[str, Dict[str, float]] = {}

    for tx in rows:
        ttype = (tx.type or "").lower()
        amt = _to_float(tx.amount)
        prov = (tx.provider or "unknown")

        # day key in UTC
        day = None
        if tx.created_at:
            dt = tx.created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            day = dt.astimezone(timezone.utc).strftime("%Y-%m-%d")

        if ttype == "deposit":
            total_deposit += amt
        elif ttype == "withdrawal":
            total_withdrawal += amt

        provider_breakdown[prov] = provider_breakdown.get(prov, 0.0) + amt

        if day:
            buckets.setdefault(day, {"deposits": 0.0, "withdrawals": 0.0})
            if ttype == "deposit":
                buckets[day]["deposits"] += amt
            elif ttype == "withdrawal":
                buckets[day]["withdrawals"] += amt

    # Deterministic daily_stats: last 7 days (UTC)
    now = datetime.now(timezone.utc)
    base = now.date()
    daily_stats: List[Dict[str, Any]] = []
    for i in range(6, -1, -1):
        day_dt = datetime(base.year, base.month, base.day, tzinfo=timezone.utc) - timedelta(days=i)
        day = day_dt.strftime("%Y-%m-%d")
        b = buckets.get(day, {"deposits": 0.0, "withdrawals": 0.0})
        daily_stats.append({"date": day, "deposits": round(b["deposits"], 2), "withdrawals": round(b["withdrawals"], 2)})

    ggr = total_deposit - total_withdrawal

    # P0: costs mocked/deterministic
    bonus_cost = 0.0
    provider_cost = 0.0
    payment_fees = 0.0
    chargeback_amount = 0.0
    chargeback_count = 0
    fx_impact = 0.0

    ngr = ggr - (bonus_cost + provider_cost + payment_fees + chargeback_amount)

    provider_breakdown_out = {k: round(v, 2) for k, v in provider_breakdown.items()} or {"unknown": 0.0}

    return {
        "ggr": round(ggr, 2),
        "ngr": round(ngr, 2),
        "total_deposit": round(total_deposit, 2),
        "total_withdrawal": round(total_withdrawal, 2),
        "provider_breakdown": provider_breakdown_out,
        "daily_stats": daily_stats,
        "bonus_cost": bonus_cost,
        "provider_cost": provider_cost,
        "payment_fees": payment_fees,
        "chargeback_amount": chargeback_amount,
        "chargeback_count": chargeback_count,
        "fx_impact": fx_impact,
    }
