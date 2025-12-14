from fastapi import APIRouter, Depends, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import Affiliate, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/affiliates", tags=["affiliates"])

@router.get("/")
async def get_affiliates(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(Affiliate).where(Affiliate.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    items = result.scalars().all()
    # Frontend AffiliateManagement.jsx expects direct array: setAffiliates((await api.get('/v1/affiliates')).data);
    return items

@router.post("/")
async def create_affiliate(
    affiliate_data: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    aff = Affiliate(
        tenant_id=current_admin.tenant_id,
        username=affiliate_data["username"],
        email=affiliate_data["email"],
        commission_rate=affiliate_data.get("commission_rate", 0.0)
    )
    session.add(aff)
    await session.commit()
    await session.refresh(aff)
    return aff

# Stubs returning arrays
@router.get("/offers")
async def get_offers(): return []

@router.get("/links")
async def get_links(): return []

@router.get("/payouts")
async def get_payouts(): return []

@router.get("/creatives")
async def get_creatives(): return []
