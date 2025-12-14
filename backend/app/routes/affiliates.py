from fastapi import APIRouter, Depends, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import Affiliate, AdminUser
from app.utils.auth import get_current_admin
from app.services.feature_access import enforce_module_access
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/affiliates", tags=["affiliates"])

@router.get("")
async def get_affiliates(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    query = select(Affiliate).where(Affiliate.tenant_id == tenant_id)
    result = await session.execute(query)
    items = result.scalars().all()
    # Frontend AffiliateManagement.jsx expects direct array: setAffiliates((await api.get('/v1/affiliates')).data);
    return items

@router.post("")
async def create_affiliate(
    request: Request,
    affiliate_data: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    # UI sends: { username, email, company_name, model }
    aff = Affiliate(
        tenant_id=tenant_id,
        name=affiliate_data.get("username") or affiliate_data.get("name") or "",
        email=affiliate_data.get("email") or "",
        status="active",
    )
    session.add(aff)
    await session.commit()
    await session.refresh(aff)
    return aff

# Stubs returning arrays
@router.get("/offers")
async def get_offers(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []

@router.get("/links")
async def get_links(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []


@router.get("/payouts")
async def get_payouts(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []


@router.get("/creatives")
async def get_creatives(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []
