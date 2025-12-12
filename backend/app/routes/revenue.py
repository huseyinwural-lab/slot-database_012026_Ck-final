"""
Revenue and financial reporting endpoints
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel

from config import settings
from app.models.domain.admin import AdminUser
from app.utils.auth import get_current_admin
from app.utils.permissions import is_owner, require_owner


router = APIRouter(prefix="/api/v1/reports", tags=["revenue"])


def get_db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


# --- RESPONSE MODELS ---

class TenantRevenue(BaseModel):
    tenant_id: str
    tenant_name: Optional[str] = None
    total_bets: float = 0.0
    total_wins: float = 0.0
    ggr: float = 0.0  # Gross Gaming Revenue = bets - wins
    transaction_count: int = 0


class RevenueResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    tenants: List[TenantRevenue]
    total_ggr: float = 0.0


class MyTenantRevenue(BaseModel):
    tenant_id: str
    total_bets: float = 0.0
    total_wins: float = 0.0
    ggr: float = 0.0
    transaction_count: int = 0
    period_start: datetime
    period_end: datetime


# --- OWNER ENDPOINTS ---

@router.get("/revenue/all-tenants", response_model=RevenueResponse)
async def get_all_tenants_revenue(
    from_date: Optional[datetime] = Query(None, description="Start date (default: 7 days ago)"),
    to_date: Optional[datetime] = Query(None, description="End date (default: now)"),
    tenant_id: Optional[str] = Query(None, description="Filter by specific tenant"),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Owner-only: Get revenue for all tenants
    
    Returns aggregated revenue by tenant with filtering options
    """
    require_owner(current_admin)
    
    db = get_db()
    
    # Default date range: last 7 days
    if not from_date:
        from_date = datetime.now(timezone.utc) - timedelta(days=7)
    if not to_date:
        to_date = datetime.now(timezone.utc)
    
    # Build query
    query = {
        "created_at": {"$gte": from_date, "$lte": to_date},
        "type": {"$in": ["bet", "win"]}  # Filter relevant transaction types
    }
    
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    # Aggregate by tenant
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$tenant_id",
            "total_bets": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "bet"]}, "$amount", 0]
                }
            },
            "total_wins": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "win"]}, "$amount", 0]
                }
            },
            "transaction_count": {"$sum": 1}
        }},
        {"$project": {
            "tenant_id": "$_id",
            "total_bets": 1,
            "total_wins": 1,
            "ggr": {"$subtract": ["$total_bets", "$total_wins"]},
            "transaction_count": 1
        }},
        {"$sort": {"ggr": -1}}  # Sort by GGR descending
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(None)
    
    # Enrich with tenant names
    tenant_revenues = []
    for r in results:
        tenant = await db.tenants.find_one({"id": r["tenant_id"]}, {"_id": 0, "name": 1})
        tenant_revenues.append(TenantRevenue(
            tenant_id=r["tenant_id"],
            tenant_name=tenant["name"] if tenant else "Unknown",
            total_bets=r["total_bets"],
            total_wins=r["total_wins"],
            ggr=r["ggr"],
            transaction_count=r["transaction_count"]
        ))
    
    # Calculate total GGR
    total_ggr = sum(t.ggr for t in tenant_revenues)
    
    return RevenueResponse(
        period_start=from_date,
        period_end=to_date,
        tenants=tenant_revenues,
        total_ggr=total_ggr
    )


# --- TENANT ENDPOINTS ---

@router.get("/revenue/my-tenant", response_model=MyTenantRevenue)
async def get_my_tenant_revenue(
    from_date: Optional[datetime] = Query(None, description="Start date (default: 7 days ago)"),
    to_date: Optional[datetime] = Query(None, description="End date (default: now)"),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Tenant: Get revenue for own tenant only
    
    Returns aggregated revenue metrics for the current admin's tenant
    """
    db = get_db()
    
    # Tenant can only see their own data
    tenant_id = current_admin.tenant_id
    
    # Default date range: last 7 days
    if not from_date:
        from_date = datetime.now(timezone.utc) - timedelta(days=7)
    if not to_date:
        to_date = datetime.now(timezone.utc)
    
    # Build query
    query = {
        "tenant_id": tenant_id,
        "created_at": {"$gte": from_date, "$lte": to_date},
        "type": {"$in": ["bet", "win"]}
    }
    
    # Aggregate
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_bets": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "bet"]}, "$amount", 0]
                }
            },
            "total_wins": {
                "$sum": {
                    "$cond": [{"$eq": ["$type", "win"]}, "$amount", 0]
                }
            },
            "transaction_count": {"$sum": 1}
        }},
        {"$project": {
            "total_bets": 1,
            "total_wins": 1,
            "ggr": {"$subtract": ["$total_bets", "$total_wins"]},
            "transaction_count": 1
        }}
    ]
    
    result = await db.transactions.aggregate(pipeline).to_list(1)
    
    if result:
        data = result[0]
        return MyTenantRevenue(
            tenant_id=tenant_id,
            total_bets=data["total_bets"],
            total_wins=data["total_wins"],
            ggr=data["ggr"],
            transaction_count=data["transaction_count"],
            period_start=from_date,
            period_end=to_date
        )
    else:
        # No data for period
        return MyTenantRevenue(
            tenant_id=tenant_id,
            total_bets=0.0,
            total_wins=0.0,
            ggr=0.0,
            transaction_count=0,
            period_start=from_date,
            period_end=to_date
        )
