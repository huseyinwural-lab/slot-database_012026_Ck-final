from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.bonus_models import BonusCampaign, BonusCampaignGame, BonusGrant
from app.models.sql_models import AdminUser
from app.services.audit import audit
from app.services.bonus_engine import (
    BONUS_TYPES_P0,
    consume_free_use,
    grant_campaign_to_player,
    get_onboarding_campaign,
)


def _now_utc_naive() -> datetime:
    return datetime.utcnow()


async def _audit_best_effort(
    *,
    session: AsyncSession,
    request: Request,
    admin: Optional[AdminUser],
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    reason: str,
    result: str,
    details: dict,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    try:
        await audit.log_event(
            session=session,
            request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
            actor_user_id=str(getattr(admin, "id", "system")),
            actor_role=getattr(admin, "role", None),
            tenant_id=str(tenant_id),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            status="SUCCESS" if result == "success" else "FAILED",
            reason=reason,
            details=details,
            before=before,
            after=after,
            error_code=error_code,
            error_message=error_message,
            ip_address=getattr(request.state, "ip_address", None),
            user_agent=getattr(request.state, "user_agent", None),
        )
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass


async def create_campaign_with_games(
    session: AsyncSession,
    *,
    tenant_id: str,
    admin: AdminUser,
    request: Request,
    name: str,
    bonus_type: str,
    status: str,
    game_ids: list[str],
    bet_amount: Optional[float],
    spin_count: Optional[int],
    max_uses: Optional[int],
    config: dict,
    reason: str,
) -> BonusCampaign:
    if bonus_type not in BONUS_TYPES_P0:
        raise HTTPException(status_code=400, detail={"error_code": "BONUS_TYPE_INVALID"})

    campaign = BonusCampaign(
        tenant_id=tenant_id,
        name=name,
        bonus_type=bonus_type,
        type=bonus_type,
        status=status,
        bet_amount=bet_amount,
        spin_count=spin_count,
        max_uses=max_uses,
        config=config or {},
        start_date=None,
        end_date=None,
    )

    session.add(campaign)
    await session.flush()

    for gid in game_ids or []:
        session.add(BonusCampaignGame(campaign_id=campaign.id, game_id=str(gid)))

    await _audit_best_effort(
        session=session,
        request=request,
        admin=admin,
        tenant_id=tenant_id,
        action="BONUS_CAMPAIGN_CREATE",
        resource_type="bonus_campaign",
        resource_id=campaign.id,
        reason=reason,
        result="success",
        details={"name": name, "bonus_type": bonus_type, "game_ids": list(game_ids or [])},
    )

    return campaign


async def list_campaigns_with_games(session: AsyncSession, *, tenant_id: str) -> list[dict]:
    stmt = select(BonusCampaign).where(BonusCampaign.tenant_id == tenant_id)
    campaigns = (await session.execute(stmt)).scalars().all()

    out: list[dict] = []
    for c in campaigns:
        map_stmt = select(BonusCampaignGame.game_id).where(BonusCampaignGame.campaign_id == c.id)
        game_ids = [r[0] for r in (await session.execute(map_stmt)).all()]
        out.append(
            {
                "id": c.id,
                "tenant_id": c.tenant_id,
                "name": c.name,
                "bonus_type": c.bonus_type,
                "status": c.status,
                "bet_amount": c.bet_amount,
                "spin_count": c.spin_count,
                "max_uses": c.max_uses,
                "config": c.config or {},
                "game_ids": game_ids,
            }
        )

    return out


async def set_campaign_status(
    session: AsyncSession,
    *,
    tenant_id: str,
    admin: AdminUser,
    request: Request,
    campaign_id: str,
    status: str,
    reason: str,
) -> BonusCampaign:
    c = await session.get(BonusCampaign, campaign_id)
    if not c or c.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "CAMPAIGN_NOT_FOUND"})

    before = {"status": c.status}
    c.status = status
    session.add(c)

    await _audit_best_effort(
        session=session,
        request=request,
        admin=admin,
        tenant_id=tenant_id,
        action="BONUS_CAMPAIGN_STATUS_CHANGE",
        resource_type="bonus_campaign",
        resource_id=c.id,
        reason=reason,
        result="success",
        details={"status": status},
        before=before,
        after={"status": status},
    )

    return c


async def grant_bonus_admin(
    session: AsyncSession,
    *,
    tenant_id: str,
    admin: AdminUser,
    request: Request,
    campaign_id: str,
    player_id: str,
    amount: Optional[float],
    reason: str,
) -> BonusGrant:
    campaign = await session.get(BonusCampaign, campaign_id)
    if not campaign or campaign.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "CAMPAIGN_NOT_FOUND"})

    # Guard: avoid double active grant for same campaign
    stmt = select(BonusGrant).where(
        BonusGrant.tenant_id == tenant_id,
        BonusGrant.player_id == player_id,
        BonusGrant.campaign_id == campaign_id,
        BonusGrant.status == "active",
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "GRANT_ALREADY_ACTIVE"})

    grant = await grant_campaign_to_player(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        campaign=campaign,
        reason=reason,
        created_by_admin_id=str(admin.id),
        provider_event_id=None,
        amount_override=amount,
    )

    await _audit_best_effort(
        session=session,
        request=request,
        admin=admin,
        tenant_id=tenant_id,
        action="BONUS_GRANT",
        resource_type="bonus_grant",
        resource_id=grant.id,
        reason=reason,
        result="success",
        details={"campaign_id": campaign_id, "player_id": player_id, "amount": amount},
    )

    return grant


async def consume_bonus_admin(
    session: AsyncSession,
    *,
    tenant_id: str,
    admin: AdminUser,
    request: Request,
    grant_id: str,
    reason: str,
    provider_event_id: Optional[str] = None,
) -> BonusGrant:
    grant = await session.get(BonusGrant, grant_id)
    if not grant or grant.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "GRANT_NOT_FOUND"})

    before = {"remaining_uses": grant.remaining_uses, "status": grant.status}
    updated = await consume_free_use(session, grant=grant, provider_event_id=provider_event_id)

    await _audit_best_effort(
        session=session,
        request=request,
        admin=admin,
        tenant_id=tenant_id,
        action="BONUS_CONSUME",
        resource_type="bonus_grant",
        resource_id=grant.id,
        reason=reason,
        result="success",
        details={"provider_event_id": provider_event_id},
        before=before,
        after={"remaining_uses": updated.remaining_uses, "status": updated.status},
    )

    return updated


async def forfeit_grant_admin(
    session: AsyncSession,
    *,
    tenant_id: str,
    admin: AdminUser,
    request: Request,
    grant_id: str,
    reason: str,
    action: str,  # revoke|expire
) -> BonusGrant:
    grant = await session.get(BonusGrant, grant_id)
    if not grant or grant.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail={"error_code": "GRANT_NOT_FOUND"})

    before = {"status": grant.status}
    if grant.status != "active":
        raise HTTPException(status_code=409, detail={"error_code": "GRANT_NOT_ACTIVE"})

    # Forfeit semantics (user-confirmed): remaining bonus is NOT transferred to real.
    # P0: we do not track per-grant spent amounts yet, so we can only forfeit what's
    # currently in the player's bonus snapshot.
    if grant.bonus_type == "MANUAL_CREDIT":
        from app.repositories.ledger_repo import get_balance
        from app.services.wallet_ledger import apply_bonus_delta_with_ledger

        bal = await get_balance(session, tenant_id=tenant_id, player_id=grant.player_id, currency="USD")
        current_bonus = float(getattr(bal, "balance_bonus_available", 0.0) or 0.0)
        to_forfeit = min(current_bonus, float(grant.amount_granted or 0.0))

        if to_forfeit > 0:
            await apply_bonus_delta_with_ledger(
                session,
                tenant_id=tenant_id,
                player_id=grant.player_id,
                tx_id=str(uuid.uuid4()),
                event_type="bonus_forfeited",
                delta_bonus_available=-float(to_forfeit),
                currency="USD",
                provider="bonus",
                provider_ref=reason,
                provider_event_id=f"bonus_forfeit:{grant.id}",
            )

    grant.status = "forfeited" if action == "revoke" else "expired"
    if action == "expire":
        grant.expires_at = _now_utc_naive()
    session.add(grant)

    await _audit_best_effort(
        session=session,
        request=request,
        admin=admin,
        tenant_id=tenant_id,
        action="BONUS_REVOKE" if action == "revoke" else "BONUS_EXPIRE",
        resource_type="bonus_grant",
        resource_id=grant.id,
        reason=reason,
        result="success",
        details={},
        before=before,
        after={"status": grant.status},
    )

    return grant


async def auto_grant_onboarding_if_eligible(
    session: AsyncSession,
    *,
    tenant_id: str,
    player_id: str,
) -> Optional[BonusGrant]:
    """Auto-grant onboarding bonus on register.

    Rules:
    - triggered on register
    - 1 user = 1 onboarding bonus (guard by checking any grant from onboarding campaign)
    - if onboarding campaign missing: no-op
    """

    campaign = await get_onboarding_campaign(session, tenant_id=tenant_id)
    if not campaign:
        return None

    # Guard: if user already has any grant for this campaign, do nothing.
    stmt = select(BonusGrant).where(
        BonusGrant.tenant_id == tenant_id,
        BonusGrant.player_id == player_id,
        BonusGrant.campaign_id == campaign.id,
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        return None

    grant = await grant_campaign_to_player(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        campaign=campaign,
        reason="ONBOARDING_AUTO_GRANT",
        created_by_admin_id=None,
        provider_event_id=f"onboarding:{player_id}",
    )

    return grant
