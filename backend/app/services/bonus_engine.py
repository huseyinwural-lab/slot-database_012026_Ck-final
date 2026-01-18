from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Sequence
import logging
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.bonus_models import BonusCampaign, BonusCampaignGame, BonusGrant
from app.services.wallet_ledger import apply_bonus_delta_with_ledger

logger = logging.getLogger(__name__)


BONUS_TYPES_P0 = {"FREE_SPIN", "FREE_BET", "MANUAL_CREDIT"}


def _now_utc_naive() -> datetime:
    # DB columns are naive in many places in this codebase.
    return datetime.utcnow()


def _campaign_expiry(campaign: BonusCampaign) -> Optional[datetime]:
    try:
        hours = campaign.config.get("expiry_hours")
        if hours is None:
            return None
        hours_f = float(hours)
        if hours_f <= 0:
            return None
        return _now_utc_naive() + timedelta(hours=hours_f)
    except Exception:
        return None


async def get_onboarding_campaign(session: AsyncSession, *, tenant_id: str) -> Optional[BonusCampaign]:
    """Return the single ACTIVE onboarding campaign, or None.

    Rules (user-confirmed):
    - onboarding is defined by campaign.config.is_onboarding == true and status == ACTIVE
    - if multiple found: raise 409 ONBOARDING_CAMPAIGN_AMBIGUOUS
    - if none: return None (no-op)
    """

    stmt = select(BonusCampaign).where(BonusCampaign.tenant_id == tenant_id)
    rows = (await session.execute(stmt)).scalars().all()

    onboarding = []
    for c in rows:
        try:
            is_onboarding = bool((c.config or {}).get("is_onboarding"))
        except Exception:
            is_onboarding = False
        if is_onboarding and str(c.status).lower() == "active":
            onboarding.append(c)

    if len(onboarding) > 1:
        raise HTTPException(status_code=409, detail={"error_code": "ONBOARDING_CAMPAIGN_AMBIGUOUS"})

    if not onboarding:
        return None

    return onboarding[0]


async def grant_campaign_to_player(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    campaign: BonusCampaign,
    reason: str,
    created_by_admin_id: Optional[str] = None,
    provider_event_id: Optional[str] = None,
    amount_override: Optional[float] = None,
) -> BonusGrant:
    """Create a BonusGrant and apply any wallet effects (MANUAL_CREDIT).

    - FREE_SPIN / FREE_BET: only remaining_uses is tracked.
    - MANUAL_CREDIT: credits bonus balance (WalletBalance.balance_bonus_available) and mirrors Player.balance_bonus.
    """

    bonus_type = campaign.bonus_type or campaign.type
    if bonus_type not in BONUS_TYPES_P0:
        raise HTTPException(status_code=400, detail={"error_code": "BONUS_TYPE_INVALID"})

    # Determine remaining uses for free mechanics
    remaining_uses: Optional[int] = None
    if bonus_type in {"FREE_SPIN", "FREE_BET"}:
        max_uses = campaign.max_uses
        if max_uses is None:
            # allow max_uses in config too
            max_uses = (campaign.config or {}).get("max_uses")
        try:
            remaining_uses = int(max_uses) if max_uses is not None else None
        except Exception:
            remaining_uses = None
        if remaining_uses is None or remaining_uses <= 0:
            raise HTTPException(status_code=400, detail={"error_code": "MAX_USES_REQUIRED"})

    grant_amount = 0.0
    if bonus_type == "MANUAL_CREDIT":
        amt = amount_override
        if amt is None:
            try:
                amt = float((campaign.config or {}).get("amount"))
            except Exception:
                amt = None
        if amt is None or float(amt) <= 0:
            raise HTTPException(status_code=400, detail={"error_code": "AMOUNT_REQUIRED"})
        grant_amount = float(amt)

    expires_at = _campaign_expiry(campaign)

    grant = BonusGrant(
        tenant_id=tenant_id,
        campaign_id=campaign.id,
        player_id=player_id,
        bonus_type=bonus_type,
        amount_granted=grant_amount,
        initial_balance=grant_amount,
        remaining_uses=remaining_uses,
        expires_at=expires_at,
        status="active",
    )
    session.add(grant)
    await session.flush()

    # Apply wallet side-effect for MANUAL_CREDIT
    if bonus_type == "MANUAL_CREDIT":
        tx_id = str(uuid.uuid4())
        await apply_bonus_delta_with_ledger(
            session,
            tenant_id=tenant_id,
            player_id=player_id,
            tx_id=tx_id,
            event_type="bonus_granted",
            delta_bonus_available=grant_amount,
            currency="USD",
            idempotency_key=None,
            provider="bonus",
            provider_ref=reason,
            provider_event_id=provider_event_id or f"bonus_grant:{grant.id}",
            allow_negative=False,
        )

    return grant


async def find_applicable_free_grant(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
    game_id: str,
) -> Optional[BonusGrant]:
    """Return an active FREE_SPIN/FREE_BET grant applicable to this game_id."""

    now = _now_utc_naive()

    stmt = (
        select(BonusGrant)
        .where(
            BonusGrant.tenant_id == tenant_id,
            BonusGrant.player_id == player_id,
            BonusGrant.status == "active",
            BonusGrant.bonus_type.in_(["FREE_SPIN", "FREE_BET"]),
        )
        .order_by(BonusGrant.granted_at.asc())
    )
    grants: Sequence[BonusGrant] = (await session.execute(stmt)).scalars().all()

    for g in grants:
        # expiry guard
        if g.expires_at and g.expires_at < now:
            continue
        if g.remaining_uses is None or g.remaining_uses <= 0:
            continue

        # game scope guard
        stmt_map = select(BonusCampaignGame).where(
            BonusCampaignGame.campaign_id == g.campaign_id,
            BonusCampaignGame.game_id == game_id,
        )
        mapped = (await session.execute(stmt_map)).scalars().first()
        if mapped:
            return g

    return None


async def consume_free_use(
    session: AsyncSession,
    *,
    grant: BonusGrant,
    provider_event_id: Optional[str] = None,
) -> BonusGrant:
    if grant.status != "active":
        raise HTTPException(status_code=409, detail={"error_code": "GRANT_NOT_ACTIVE"})

    now = _now_utc_naive()
    if grant.expires_at and grant.expires_at < now:
        grant.status = "expired"
        session.add(grant)
        return grant

    if grant.remaining_uses is None or grant.remaining_uses <= 0:
        raise HTTPException(status_code=409, detail={"error_code": "NO_REMAINING_USES"})

    grant.remaining_uses = int(grant.remaining_uses) - 1
    if grant.remaining_uses <= 0:
        grant.remaining_uses = 0
        grant.status = "completed"
        grant.completed_at = now

    session.add(grant)
    return grant
