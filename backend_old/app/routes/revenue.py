from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.database import get_session
from app.models.sql_models import Transaction, Tenant, AdminUser
from app.utils.auth import get_current_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/reports", tags=["revenue"])

class TenantRevenueResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    total_bets: float
    total_wins: float
    ggr: float
    transaction_count: int

class RevenueResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    tenants: List[TenantRevenueResponse]
    total_ggr: float

@router.get("/revenue/all-tenants", response_model=RevenueResponse)
async def get_all_tenants_revenue(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    tenant_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=7)
    if not to_date:
        to_date = datetime.utcnow()

    # 1. Get Tenants
    tenant_query = select(Tenant)
    if tenant_id:
        tenant_query = tenant_query.where(Tenant.id == tenant_id)
    
    tenants = (await session.execute(tenant_query)).scalars().all()
    
    results = []
    total_platform_ggr = 0.0

    for t in tenants:
        # Calculate Revenue per Tenant
        # Bet Sum
        bet_q = select(func.sum(Transaction.amount)).where(
            Transaction.tenant_id == t.id,
            Transaction.type == "bet",
            Transaction.created_at >= from_date,
            Transaction.created_at <= to_date
        )
        total_bets = (await session.execute(bet_q)).scalar() or 0.0

        # Win Sum
        win_q = select(func.sum(Transaction.amount)).where(
            Transaction.tenant_id == t.id,
            Transaction.type == "win",
            Transaction.created_at >= from_date,
            Transaction.created_at <= to_date
        )
        total_wins = (await session.execute(win_q)).scalar() or 0.0
        
        # Count
        count_q = select(func.count()).where(
            Transaction.tenant_id == t.id,
            Transaction.created_at >= from_date,
            Transaction.created_at <= to_date
        )
        tx_count = (await session.execute(count_q)).scalar() or 0

        ggr = total_bets - total_wins
        total_platform_ggr += ggr

        results.append(TenantRevenueResponse(
            tenant_id=t.id,
            tenant_name=t.name,
            total_bets=total_bets,
            total_wins=total_wins,
            ggr=ggr,
            transaction_count=tx_count
        ))

    return RevenueResponse(
        period_start=from_date,
        period_end=to_date,
        tenants=results,
        total_ggr=total_platform_ggr
    )

class MyTenantRevenue(BaseModel):
    tenant_id: str
    total_bets: float = 0.0
    total_wins: float = 0.0
    ggr: float = 0.0
    transaction_count: int = 0
    period_start: datetime
    period_end: datetime

@router.get("/revenue/my-tenant", response_model=MyTenantRevenue)
async def get_my_tenant_revenue(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=7)
    if not to_date:
        to_date = datetime.utcnow()
        
    tenant_id = current_admin.tenant_id
    
    bet_q = select(func.sum(Transaction.amount)).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "bet",
        Transaction.created_at >= from_date,
        Transaction.created_at <= to_date
    )
    total_bets = (await session.execute(bet_q)).scalar() or 0.0

    win_q = select(func.sum(Transaction.amount)).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "win",
        Transaction.created_at >= from_date,
        Transaction.created_at <= to_date
    )
    total_wins = (await session.execute(win_q)).scalar() or 0.0
    
    count_q = select(func.count()).where(
        Transaction.tenant_id == tenant_id,
        Transaction.created_at >= from_date,
        Transaction.created_at <= to_date
    )
    tx_count = (await session.execute(count_q)).scalar() or 0
    
    return MyTenantRevenue(
        tenant_id=tenant_id,
        total_bets=total_bets,
        total_wins=total_wins,
        ggr=total_bets - total_wins,
        transaction_count=tx_count,
        period_start=from_date,
        period_end=to_date
    )
