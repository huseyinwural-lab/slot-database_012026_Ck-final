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

from app.services.rbac import require_ops

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
    """Back-compat endpoint (deprecated). Creates a partner and returns it."""
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    name = affiliate_data.get("username") or affiliate_data.get("name") or ""
    email = affiliate_data.get("email") or ""
    if not name or not email:
        raise HTTPException(status_code=400, detail={"error_code": "VALIDATION_ERROR"})

    partner = await create_partner(session, tenant_id=tenant_id, name=name, email=email)
    partner.status = "active"
    session.add(partner)
    await session.commit()
    await session.refresh(partner)
    return partner

@router.get("/{affiliate_id}/links")
async def get_affiliate_links(
    affiliate_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    stmt = select(AffiliateLink).where(AffiliateLink.tenant_id == tenant_id, AffiliateLink.affiliate_id == affiliate_id)
    links = (await session.execute(stmt)).scalars().all()

    out = []
    for link in links:
        out.append(
            {
                "id": link.id,
                "code": link.code,
                "tracking_url": make_tracking_url(link.code),
                "offer_id": link.offer_id,
                "landing_path": link.landing_path,
                "currency": link.currency,
                "expires_at": link.expires_at,
                "clicks": link.clicks,
                "signups": link.signups,
                "created_at": link.created_at,
            }
        )

    return out

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

# --- AFFILIATE P0 ENDPOINTS ---

@router.get("/partners", response_model=List[PartnerOut])
async def list_partners(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    stmt = select(Affiliate).where(Affiliate.tenant_id == tenant_id)
    partners = (await session.execute(stmt)).scalars().all()

    # Compute balances by currency from affiliateledger.
    balances = await compute_partner_balances(session, tenant_id=tenant_id)

    out = []
    for p in partners:
        cur = balances.get(p.id) or {}
        # P0: UI shows single numeric balance; keep it USD for now.
        bal = 0.0
        try:
            bal = float(cur.get("USD", 0.0))
        except Exception:
            bal = 0.0

        out.append(
            PartnerOut(
                id=p.id,
                tenant_id=p.tenant_id,
                code=getattr(p, "code", None),
                username=p.username,
                email=p.email,
                status=p.status,
                created_at=p.created_at,
                balance=bal,
                company_name=getattr(p, "company_name", None),
            )
        )

    return out


@router.post("/partners", response_model=PartnerOut)
async def add_partner(
    request: Request,
    payload: PartnerCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    require_ops(current_admin)

    partner = await create_partner(session, tenant_id=tenant_id, name=payload.name, email=payload.email)
    await session.commit()
    await session.refresh(partner)
    return partner


@router.post("/partners/{partner_id}/activate", response_model=PartnerOut)
async def activate_partner(
    partner_id: str,
    request: Request,
    payload: PartnerStatusRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    partner = await set_partner_status(session, tenant_id=tenant_id, partner_id=partner_id, status="active")
    await session.commit()
    await session.refresh(partner)
    return partner


@router.post("/partners/{partner_id}/deactivate", response_model=PartnerOut)
async def deactivate_partner(
    partner_id: str,
    request: Request,
    payload: PartnerStatusRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    partner = await set_partner_status(session, tenant_id=tenant_id, partner_id=partner_id, status="inactive")
    await session.commit()
    await session.refresh(partner)
    return partner


@router.get("/offers", response_model=List[OfferOut])
async def list_offers(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    stmt = select(AffiliateOffer).where(AffiliateOffer.tenant_id == tenant_id).order_by(AffiliateOffer.created_at.desc())
    return (await session.execute(stmt)).scalars().all()


@router.post("/offers", response_model=OfferOut)
async def create_offer_route(
    request: Request,
    payload: OfferCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    offer = await create_offer(
        session,
        tenant_id=tenant_id,
        name=payload.name,
        model=payload.model,
        currency=payload.currency,
        cpa_amount=payload.cpa_amount,
        min_deposit=payload.min_deposit,
    )
    await session.commit()
    await session.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/activate", response_model=OfferOut)
async def activate_offer(
    offer_id: str,
    request: Request,
    payload: OfferStatusRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    offer = await set_offer_status(session, tenant_id=tenant_id, offer_id=offer_id, status="active")
    await session.commit()
    await session.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/pause", response_model=OfferOut)
async def pause_offer(
    offer_id: str,
    request: Request,
    payload: OfferStatusRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    offer = await set_offer_status(session, tenant_id=tenant_id, offer_id=offer_id, status="paused")
    await session.commit()
    await session.refresh(offer)
    return offer


@router.post("/tracking-links", response_model=TrackingLinkOut)
async def create_tracking_link(
    request: Request,
    payload: TrackingLinkCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    link = await generate_tracking_link(
        session,
        tenant_id=tenant_id,
        partner_id=payload.partner_id,
        offer_id=payload.offer_id,
        landing_path=payload.landing_path,
        reason=payload.reason,
    )
    await session.commit()
    await session.refresh(link)

    return TrackingLinkOut(code=link.code, tracking_url=make_tracking_url(link.code), expires_at=link.expires_at)


@router.get("/r/{code}", response_model=ResolveOut)
async def resolve_tracking_code(
    code: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    # Public-ish resolve: no admin auth. Tenant is derived from header if present.
    tenant_id = request.headers.get("X-Tenant-ID") or "default_casino"

    resolved = await resolve_link(session, tenant_id=tenant_id, code=code)

    # Count click
    stmt = select(AffiliateLink).where(AffiliateLink.tenant_id == tenant_id, AffiliateLink.code == code)
    link = (await session.execute(stmt)).scalars().first()
    if link:
        link.clicks = int(link.clicks or 0) + 1
        session.add(link)
        await session.commit()

    return resolved


@router.get("/payouts", response_model=List[PayoutOut])
async def get_payouts(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    stmt = select(AffiliatePayout).where(AffiliatePayout.tenant_id == tenant_id).order_by(AffiliatePayout.created_at.desc()).limit(200)
    return (await session.execute(stmt)).scalars().all()


@router.post("/payouts", response_model=PayoutOut)
async def create_payout(
    request: Request,
    payload: PayoutCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")
    require_ops(current_admin)

    payout = await record_payout(
        session,
        tenant_id=tenant_id,
        partner_id=payload.partner_id,
        amount=payload.amount,
        currency=payload.currency,
        method=payload.method,
        reference=payload.reference,
        reason=payload.reason,
    )
    await session.commit()
    await session.refresh(payout)
    return payout


@router.get("/creatives", response_model=List[CreativeOut])
async def get_creatives(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    stmt = select(AffiliateCreative).where(AffiliateCreative.tenant_id == tenant_id).order_by(AffiliateCreative.created_at.desc()).limit(200)
    return (await session.execute(stmt)).scalars().all()


@router.post("/creatives", response_model=CreativeOut)
async def create_creative_route(
    request: Request,
    payload: CreativeCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    c = await create_creative(
        session,
        tenant_id=tenant_id,
        name=payload.name,
        type=payload.type,
        url=payload.url,
        size=payload.size,
        language=payload.language,
    )
    await session.commit()
    await session.refresh(c)
    return c


@router.get("/reports/summary", response_model=ReportSummaryOut)
async def reports_summary(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="affiliates")

    return await summary_report(session, tenant_id=tenant_id)
