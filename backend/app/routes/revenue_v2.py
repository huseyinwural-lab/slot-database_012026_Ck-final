from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from pydantic import BaseModel

from app.core.database import get_session
from app.models.sql_models import Transaction, Tenant, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/revenue", tags=["revenue"])


class TenantRevenueItem(BaseModel):
    tenant_id: str
    tenant_name: str
    total_bets: float
    total_wins: float
    ggr: float
    transaction_count: int


class RevenueTotals(BaseModel):
    total_ggr: float
    total_bets: float
    total_wins: float
    tenant_count: int


class RevenueMeta(BaseModel):
    range_days: int
    period_start: datetime
    period_end: datetime


class AllTenantsRevenueResponse(BaseModel):
    items: List[TenantRevenueItem]
    totals: RevenueTotals
    meta: RevenueMeta

    # Backward-compat for existing UI patterns
    tenants: List[TenantRevenueItem]
    total_ggr: float
    period_start: datetime
    period_end: datetime


def _require_owner(current_admin: AdminUser) -> None:
    if not getattr(current_admin, "is_platform_owner", False):
        raise HTTPException(status_code=403, detail={"error_code": "OWNER_ONLY"})


def _parse_range_days(range_days: int) -> int:
    if range_days not in {1, 7, 30}:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_RANGE_DAYS"})
    return range_days


@router.get("/all-tenants", response_model=AllTenantsRevenueResponse)
async def get_all_tenants_revenue_v2(
    request: Request,
    range_days: int = Query(7),
    tenant_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Owner-only platform revenue aggregate.

    Deterministic contract:
      - range_days must be 1/7/30
      - meta contains period_start/period_end
      - cache-safety: response varies by range_days

    Notes:
      - Aggregation uses Transaction types: bet / win
    """

    _require_owner(current_admin)
    safe_range = _parse_range_days(int(range_days))

    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=safe_range)

    tenant_query = select(Tenant)
    if tenant_id:
        tenant_query = tenant_query.where(Tenant.id == tenant_id)

    tenants = (await session.execute(tenant_query)).scalars().all()

    items: List[TenantRevenueItem] = []
    total_platform_ggr = 0.0
    total_platform_bets = 0.0
    total_platform_wins = 0.0

    for t in tenants:
        bet_q = select(func.sum(Transaction.amount)).where(
            Transaction.tenant_id == t.id,
            Transaction.type == "bet",
            Transaction.created_at >= period_start,
            Transaction.created_at <= period_end,
        )
        total_bets = float((await session.execute(bet_q)).scalar() or 0.0)

        win_q = select(func.sum(Transaction.amount)).where(
            Transaction.tenant_id == t.id,
            Transaction.type == "win",
            Transaction.created_at >= period_start,
            Transaction.created_at <= period_end,
        )
        total_wins = float((await session.execute(win_q)).scalar() or 0.0)

        count_q = select(func.count()).where(
            Transaction.tenant_id == t.id,
            Transaction.created_at >= period_start,
            Transaction.created_at <= period_end,
        )
        tx_count = int((await session.execute(count_q)).scalar() or 0)

        ggr = float(total_bets - total_wins)

        total_platform_bets += total_bets
        total_platform_wins += total_wins
        total_platform_ggr += ggr

        items.append(
            TenantRevenueItem(
                tenant_id=t.id,
                tenant_name=t.name,
                total_bets=total_bets,
                total_wins=total_wins,
                ggr=ggr,
                transaction_count=tx_count,
            )
        )

    meta = RevenueMeta(range_days=safe_range, period_start=period_start, period_end=period_end)
    totals = RevenueTotals(
        total_ggr=total_platform_ggr,
        total_bets=total_platform_bets,
        total_wins=total_platform_wins,
        tenant_count=len(items),
    )

    return AllTenantsRevenueResponse(
        items=items,
        totals=totals,
        meta=meta,
        tenants=items,
        total_ggr=total_platform_ggr,
        period_start=period_start,
        period_end=period_end,
    )
