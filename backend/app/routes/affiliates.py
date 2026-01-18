from app.models.growth_models import Affiliate, AffiliateLink, AffiliateAttribution
from app.services.affiliate_engine import AffiliateEngine
from app.services.affiliate_p0_engine import (
    accrue_on_first_deposit,
    compute_partner_balances,
    create_creative,
    create_offer,
    create_partner,
    generate_tracking_link,
    make_tracking_url,
    record_payout,
    resolve_link,
    set_offer_status,
    set_partner_status,
    summary_report,
)
from app.models.affiliate_p0_models import AffiliateOffer, AffiliatePayout, AffiliateCreative
from app.models.affiliate_p0_schemas import (
    CreativeCreate,
    CreativeOut,
    OfferCreate,
    OfferOut,
    OfferStatusRequest,
    PartnerCreate,
    PartnerOut,
    PartnerStatusRequest,
    PayoutCreate,
    PayoutOut,
    ReportSummaryOut,
    ResolveOut,
    TrackingLinkCreate,
    TrackingLinkOut,
)
from fastapi import APIRouter, Depends, Body, Request, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import AdminUser
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
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    # UI sends: { username, email, company_name, model }
    aff = Affiliate(
        tenant_id=tenant_id,
        username=affiliate_data.get("username") or affiliate_data.get("name") or "",
        email=affiliate_data.get("email") or "",
        commission_type=affiliate_data.get("model", "CPA"),
        cpa_amount=float(affiliate_data.get("cpa_amount", 50.0)),
        status="active",
    )
    session.add(aff)
    await session.commit()
    await session.refresh(aff)
    return aff

@router.get("/{affiliate_id}/links")
async def get_affiliate_links(
    affiliate_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    
    stmt = select(AffiliateLink).where(AffiliateLink.affiliate_id == affiliate_id, AffiliateLink.tenant_id == tenant_id)
    return (await session.execute(stmt)).scalars().all()

@router.post("/{affiliate_id}/links")
async def create_affiliate_link(
    affiliate_id: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    
    # Check affiliate
    aff = await session.get(Affiliate, affiliate_id)
    if not aff or aff.tenant_id != tenant_id:
        raise HTTPException(404, "Affiliate not found")

    code = payload.get("code")
    if not code:
        raise HTTPException(400, "Code required")
        
    # Check duplicate code
    stmt = select(AffiliateLink).where(AffiliateLink.code == code, AffiliateLink.tenant_id == tenant_id)
    if (await session.execute(stmt)).scalars().first():
        raise HTTPException(400, "Code already in use")

    link = AffiliateLink(
        tenant_id=tenant_id,
        affiliate_id=affiliate_id,
        code=code,
        campaign=payload.get("campaign", "default")
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link

# Stubs returning arrays
@router.get("/offers")
async def get_offers(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []

@router.get("/payouts")
async def get_payouts(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []


@router.get("/creatives")
async def get_creatives(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    return []
