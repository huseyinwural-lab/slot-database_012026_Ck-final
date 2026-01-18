from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.affiliate_p0_models import AffiliateCreative, AffiliateLedger, AffiliateOffer, AffiliatePayout
from app.models.growth_models import Affiliate, AffiliateAttribution, AffiliateLink


def _now() -> datetime:
    return datetime.utcnow()


def _new_partner_code() -> str:
    return f"aff_{uuid.uuid4().hex[:8]}"


async def create_partner(session: AsyncSession, *, tenant_id: str, name: str, email: str) -> Affiliate:
    # unique email guard (tenant scoped)
    stmt = select(Affiliate).where(Affiliate.tenant_id == tenant_id, Affiliate.email == email)
    if (await session.execute(stmt)).scalars().first():
        raise HTTPException(status_code=409, detail={"error_code": "PARTNER_EMAIL_EXISTS"})

    # unique code guard
    for _ in range(5):
        code = _new_partner_code()
        stmt_code = select(Affiliate).where(Affiliate.tenant_id == tenant_id, Affiliate.code == code)
        if not (await session.execute(stmt_code)).scalars().first():
            break
    else:
        raise HTTPException(status_code=500, detail={"error_code": "PARTNER_CODE_GENERATION_FAILED"})

    partner = Affiliate(
        tenant_id=tenant_id,
        username=name,
        email=email,
        code=code,
        status="inactive",
    )
    session.add(partner)
    await session.flush()
    return partner


async def set_partner_status(session: AsyncSession, *, tenant_id: str, partner_id: str, status: str) -> Affiliate:
    partner = await session.get(Affiliate, partner_id)
    if not partner or partner.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "PARTNER_NOT_FOUND"})
    partner.status = status
    session.add(partner)
    return partner


async def create_offer(session: AsyncSession, *, tenant_id: str, name: str, model: str, currency: str, cpa_amount: Optional[float], min_deposit: Optional[float]) -> AffiliateOffer:
    # unique offer name per tenant
    stmt = select(AffiliateOffer).where(AffiliateOffer.tenant_id == tenant_id, AffiliateOffer.name == name)
    if (await session.execute(stmt)).scalars().first():
        raise HTTPException(status_code=409, detail={"error_code": "OFFER_NAME_EXISTS"})

    if model.upper() not in {"CPA", "REVSHARE"}:
        raise HTTPException(status_code=400, detail={"error_code": "OFFER_MODEL_INVALID"})

    offer = AffiliateOffer(
        tenant_id=tenant_id,
        name=name,
        model=model.lower(),
        currency=currency.upper(),
        cpa_amount=cpa_amount,
        min_deposit=min_deposit,
        status="paused",
        created_at=_now(),
    )
    session.add(offer)
    await session.flush()
    return offer


async def set_offer_status(session: AsyncSession, *, tenant_id: str, offer_id: str, status: str) -> AffiliateOffer:
    offer = await session.get(AffiliateOffer, offer_id)
    if not offer or offer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "OFFER_NOT_FOUND"})

    offer.status = status
    session.add(offer)
    return offer


async def generate_tracking_link(
    session: AsyncSession,
    *,
    tenant_id: str,
    partner_id: str,
    offer_id: str,
    landing_path: str,
    reason: str,
) -> AffiliateLink:
    partner = await session.get(Affiliate, partner_id)
    if not partner or partner.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "PARTNER_NOT_FOUND"})

    offer = await session.get(AffiliateOffer, offer_id)
    if not offer or offer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "OFFER_NOT_FOUND"})

    if offer.status != "active":
        raise HTTPException(status_code=409, detail={"error_code": "OFFER_NOT_ACTIVE"})

    # Create new link each time; offer_id immutable on a given link.
    code = f"aff_{uuid.uuid4().hex[:8]}"

    expires_at = _now() + timedelta(days=90)

    link = AffiliateLink(
        tenant_id=tenant_id,
        affiliate_id=partner.id,
        code=code,
        offer_id=offer.id,
        landing_path=landing_path or "/",
        currency=offer.currency,
        expires_at=expires_at,
        campaign="generated",
        created_at=_now(),
    )
    session.add(link)
    await session.flush()
    return link


async def resolve_link(session: AsyncSession, *, tenant_id: str, code: str) -> dict:
    stmt = select(AffiliateLink).where(AffiliateLink.tenant_id == tenant_id, AffiliateLink.code == code)
    link = (await session.execute(stmt)).scalars().first()
    if not link:
        raise HTTPException(status_code=404, detail={"error_code": "LINK_NOT_FOUND"})

    if link.expires_at and link.expires_at < _now():
        raise HTTPException(status_code=410, detail={"error_code": "LINK_EXPIRED"})

    # ensure offer still exists
    if not link.offer_id:
        raise HTTPException(status_code=409, detail={"error_code": "LINK_MISSING_OFFER"})

    offer = await session.get(AffiliateOffer, link.offer_id)
    if not offer or offer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "OFFER_NOT_FOUND"})

    return {
        "landing_path": link.landing_path or "/",
        "partner_id": link.affiliate_id,
        "offer_id": link.offer_id,
        "currency": offer.currency,
        "expires_at": link.expires_at,
    }


async def bind_attribution_on_register(session: AsyncSession, *, tenant_id: str, player_id: str, affiliate_code_cookie: Optional[str]) -> None:
    if not affiliate_code_cookie:
        return

    # cookie format: code|offer_id|ts
    parts = affiliate_code_cookie.split("|")
    if not parts:
        return

    code = parts[0]

    # immutable: do not overwrite existing attribution
    stmt = select(AffiliateAttribution).where(AffiliateAttribution.tenant_id == tenant_id, AffiliateAttribution.player_id == player_id)
    if (await session.execute(stmt)).scalars().first():
        return

    stmt_link = select(AffiliateLink).where(AffiliateLink.tenant_id == tenant_id, AffiliateLink.code == code)
    link = (await session.execute(stmt_link)).scalars().first()
    if not link:
        return

    # increment signups counter
    link.signups = int(link.signups or 0) + 1
    session.add(link)

    session.add(
        AffiliateAttribution(
            tenant_id=tenant_id,
            player_id=player_id,
            affiliate_id=link.affiliate_id,
            link_id=link.id,
            attribution_type="last_click",
            status="active",
            attributed_at=_now(),
        )
    )


async def record_payout(session: AsyncSession, *, tenant_id: str, partner_id: str, amount: float, currency: str, method: str, reference: str, reason: str) -> AffiliatePayout:
    partner = await session.get(Affiliate, partner_id)
    if not partner or partner.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "PARTNER_NOT_FOUND"})

    payout = AffiliatePayout(
        tenant_id=tenant_id,
        partner_id=partner_id,
        amount=float(amount),
        currency=currency.upper(),
        method=method,
        reference=reference,
        reason=reason,
        created_at=_now(),
    )
    session.add(payout)
    await session.flush()

    session.add(
        AffiliateLedger(
            tenant_id=tenant_id,
            partner_id=partner_id,
            offer_id=None,
            player_id=None,
            entry_type="payout",
            amount=-abs(float(amount)),
            currency=currency.upper(),
            reference=reference,
            reason=reason,
            created_at=_now(),
        )
    )

    return payout


async def create_creative(session: AsyncSession, *, tenant_id: str, name: str, type: str, url: str, size: Optional[str], language: Optional[str]) -> AffiliateCreative:
    c = AffiliateCreative(
        tenant_id=tenant_id,
        name=name,
        type=type,
        url=url,
        size=size,
        language=language,
        status="active",
        created_at=_now(),
    )
    session.add(c)
    await session.flush()
    return c


async def compute_partner_balances(session: AsyncSession, *, tenant_id: str) -> dict:
    stmt = select(AffiliateLedger).where(AffiliateLedger.tenant_id == tenant_id)
    entries = (await session.execute(stmt)).scalars().all()

    # partner_id -> currency -> amount
    out: dict = {}
    for e in entries:
        out.setdefault(e.partner_id, {})
        out[e.partner_id].setdefault(e.currency, 0.0)
        out[e.partner_id][e.currency] += float(e.amount)

    return out


async def summary_report(session: AsyncSession, *, tenant_id: str) -> dict:
    # clicks/signups from links; first_deposits derived from ledger accruals
    stmt_links = select(AffiliateLink).where(AffiliateLink.tenant_id == tenant_id)
    links = (await session.execute(stmt_links)).scalars().all()
    clicks = sum(int(link.clicks or 0) for link in links)
    signups = sum(int(link.signups or 0) for link in links)

    stmt_led = select(AffiliateLedger).where(AffiliateLedger.tenant_id == tenant_id)
    entries = (await session.execute(stmt_led)).scalars().all()

    first_deposits = sum(1 for e in entries if e.entry_type == "accrual")
    payouts = sum(abs(float(e.amount)) for e in entries if e.entry_type == "payout")

    return {
        "clicks": clicks,
        "signups": signups,
        "first_deposits": first_deposits,
        "payouts": payouts,
    }


async def accrue_on_first_deposit(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    deposit_amount: float,
    currency: str,
) -> None:
    # find attribution (immutable)
    stmt_attr = select(AffiliateAttribution).where(
        AffiliateAttribution.tenant_id == tenant_id,
        AffiliateAttribution.player_id == player_id,
        AffiliateAttribution.status == "active",
    )
    attr = (await session.execute(stmt_attr)).scalars().first()
    if not attr or not attr.link_id:
        return

    link = await session.get(AffiliateLink, attr.link_id)
    if not link or link.tenant_id != tenant_id:
        return

    if not link.offer_id:
        return

    offer = await session.get(AffiliateOffer, link.offer_id)
    if not offer or offer.tenant_id != tenant_id:
        return

    # P0: only CPA on first deposit, revshare ignored.
    if offer.model != "cpa":
        return

    if offer.currency.upper() != currency.upper():
        return

    if offer.min_deposit is not None and float(deposit_amount) < float(offer.min_deposit):
        return

    # idempotency: one accrual per player+offer
    stmt_existing = select(AffiliateLedger).where(
        AffiliateLedger.tenant_id == tenant_id,
        AffiliateLedger.player_id == player_id,
        AffiliateLedger.offer_id == offer.id,
        AffiliateLedger.entry_type == "accrual",
    )
    if (await session.execute(stmt_existing)).scalars().first():
        return

    if offer.cpa_amount is None or float(offer.cpa_amount) <= 0:
        return

    session.add(
        AffiliateLedger(
            tenant_id=tenant_id,
            partner_id=link.affiliate_id,
            offer_id=offer.id,
            player_id=player_id,
            entry_type="accrual",
            amount=float(offer.cpa_amount),
            currency=offer.currency,
            reference="first_deposit",
            reason="CPA_ACCRUAL_FIRST_DEPOSIT",
            created_at=_now(),
        )
    )

    # increment first deposit count (reuse signups? no; keep in ledger)


def make_tracking_url(code: str) -> str:
    base = settings.player_app_url.rstrip("/")
    return f"{base}/r/{code}"
