from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from app.core.database import get_session
from app.models.bonus_models import BonusGrant
from app.models.bonus_schemas import (
    BonusAdminActionRequest,
    BonusCampaignCreate,
    BonusCampaignOut,
    BonusConsumeRequest,
    BonusGrantCreate,
    BonusGrantOut,
)
from app.models.sql_models import AdminUser
from app.services.bonus_lifecycle import (
    consume_bonus_admin,
    create_campaign_with_games,
    forfeit_grant_admin,
    grant_bonus_admin,
    list_campaigns_with_games,
    set_campaign_status,
)
from app.utils.auth import get_current_admin
from app.utils.reason import require_reason
from app.utils.tenant import get_current_tenant_id
from app.services.rbac import require_admin


router = APIRouter(prefix="/api/v1/bonuses", tags=["bonuses"])


@router.get("/campaigns", response_model=List[BonusCampaignOut])
async def list_campaigns(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    rows = await list_campaigns_with_games(session, tenant_id=tenant_id)
    return rows


@router.post("/campaigns", response_model=BonusCampaignOut)
async def create_campaign(
    request: Request,
    payload: BonusCampaignCreate = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    campaign = await create_campaign_with_games(
        session,
        tenant_id=tenant_id,
        admin=current_admin,
        request=request,
        name=payload.name,
        bonus_type=payload.bonus_type,
        status=payload.status,
        game_ids=payload.game_ids,
        bet_amount=payload.bet_amount,
        spin_count=payload.spin_count,
        max_uses=payload.max_uses,
        config=payload.config,
        reason=reason,
    )

    await session.commit()

    rows = await list_campaigns_with_games(session, tenant_id=tenant_id)
    # return the just-created row shape
    for r in rows:
        if r["id"] == campaign.id:
            return r
    raise HTTPException(status_code=500, detail={"error_code": "CAMPAIGN_CREATE_FAILED"})


@router.post("/campaigns/{campaign_id}/status", response_model=BonusCampaignOut)
async def update_campaign_status(
    request: Request,
    campaign_id: str,
    status: str = Body(..., embed=True),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    campaign = await set_campaign_status(
        session,
        tenant_id=tenant_id,
        admin=current_admin,
        request=request,
        campaign_id=campaign_id,
        status=status,
        reason=reason,
    )
    await session.commit()

    rows = await list_campaigns_with_games(session, tenant_id=tenant_id)
    for r in rows:
        if r["id"] == campaign.id:
            return r
    raise HTTPException(status_code=500, detail={"error_code": "CAMPAIGN_STATUS_FAILED"})


@router.post("/grant", response_model=BonusGrantOut)
async def grant_bonus(
    request: Request,
    payload: BonusGrantCreate = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    require_admin(current_admin)

    grant = await grant_bonus_admin(
        session,
        tenant_id=tenant_id,
        admin=current_admin,
        request=request,
        campaign_id=payload.campaign_id,
        player_id=payload.player_id,
        amount=payload.amount,
        reason=reason,
    )

    await session.commit()
    await session.refresh(grant)

    return BonusGrantOut.model_validate(grant)


@router.get("/players/{player_id}/bonuses", response_model=List[BonusGrantOut])
async def list_player_bonuses(
    request: Request,
    player_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    stmt = (
        select(BonusGrant)
        .where(BonusGrant.tenant_id == tenant_id, BonusGrant.player_id == player_id)
        .order_by(BonusGrant.granted_at.desc())
        .limit(200)
    )
    grants = (await session.execute(stmt)).scalars().all()
    return [BonusGrantOut.model_validate(g) for g in grants]


@router.post("/{grant_id}/consume", response_model=BonusGrantOut)
async def consume_grant(
    request: Request,
    grant_id: str,
    payload: BonusConsumeRequest = Body(default=BonusConsumeRequest()),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    grant = await consume_bonus_admin(
        session,
        tenant_id=tenant_id,
        admin=current_admin,
        request=request,
        grant_id=grant_id,
        reason=reason,
        provider_event_id=payload.provider_event_id,
    )
    await session.commit()
    await session.refresh(grant)
    return BonusGrantOut.model_validate(grant)


@router.post("/{grant_id}/revoke", response_model=BonusGrantOut)
async def revoke_grant(
    request: Request,
    grant_id: str,
    payload: BonusAdminActionRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    require_admin(current_admin)
    grant = await forfeit_grant_admin(
        session,
        tenant_id=tenant_id,
        admin=current_admin,
        request=request,
        grant_id=grant_id,
        reason=payload.reason,
        action="revoke",
    )
    await session.commit()
    await session.refresh(grant)
    return BonusGrantOut.model_validate(grant)


@router.post("/{grant_id}/expire", response_model=BonusGrantOut)
async def expire_grant(
    request: Request,
    grant_id: str,
    payload: BonusAdminActionRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    require_admin(current_admin)
    grant = await forfeit_grant_admin(
        session,
        tenant_id=tenant_id,
        admin=current_admin,
        request=request,
        grant_id=grant_id,
        reason=payload.reason,
        action="expire",
    )
    await session.commit()
    await session.refresh(grant)
    return BonusGrantOut.model_validate(grant)
