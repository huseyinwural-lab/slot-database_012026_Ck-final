from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_session
from app.models.sql_models import AdminUser, Player
from app.models.bonus_models import BonusCampaign, BonusGrant
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.audit import audit
from app.utils.reason import require_reason

router = APIRouter(prefix="/api/v1/bonuses", tags=["bonuses"])

# --- CAMPAIGNS ---

@router.get("/campaigns", response_model=List[BonusCampaign])
async def list_campaigns(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(None, current_admin, session=session)
    stmt = select(BonusCampaign).where(BonusCampaign.tenant_id == tenant_id)
    return (await session.execute(stmt)).scalars().all()

@router.post("/campaigns")
async def create_campaign(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    campaign = BonusCampaign(
        tenant_id=tenant_id,
        name=payload["name"],
        type=payload["type"],
        config=payload.get("config", {}),
        status="draft",
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date")
    )
    session.add(campaign)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=tenant_id,
        action="BONUS_CAMPAIGN_CREATE",
        resource_type="bonus_campaign",
        resource_id=campaign.id,
        result="success",
        reason=reason,
        details={"name": campaign.name, "type": campaign.type}
    )
    await session.commit()
    await session.refresh(campaign)
    return campaign

@router.post("/campaigns/{campaign_id}/status")
async def update_campaign_status(
    request: Request,
    campaign_id: str,
    status: str = Body(..., embed=True),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    campaign = await session.get(BonusCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    old_status = campaign.status
    campaign.status = status
    session.add(campaign)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        tenant_id=campaign.tenant_id,
        action="BONUS_CAMPAIGN_STATUS_CHANGE",
        resource_type="bonus_campaign",
        resource_id=campaign.id,
        result="success",
        reason=reason,
        before={"status": old_status},
        after={"status": status}
    )
    await session.commit()
    return campaign

# --- GRANTS ---

@router.post("/grant")
async def grant_bonus(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Manual Grant."""
    campaign_id = payload["campaign_id"]
    player_id = payload["player_id"]
    amount = payload.get("amount", 0.0)
    
    campaign = await session.get(BonusCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    # 1. Abuse Check (Simple Rate Limit)
    # Check if player already has an active grant for this campaign
    stmt = select(BonusGrant).where(
        BonusGrant.player_id == player_id,
        BonusGrant.campaign_id == campaign_id,
        BonusGrant.status == "active"
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(409, "Player already has an active grant for this campaign.")
        
    # 2. Config Logic
    wagering_mult = campaign.config.get("wagering_mult", 35)
    target = amount * wagering_mult
    expiry_hours = campaign.config.get("expiry_hours", 24)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
    
    grant = BonusGrant(
        tenant_id=campaign.tenant_id,
        campaign_id=campaign.id,
        player_id=player_id,
        amount_granted=amount,
        initial_balance=amount,
        wagering_target=target,
        expires_at=expires_at,
        status="active"
    )
    session.add(grant)
    
    # Update Player Balances
    player = await session.get(Player, player_id)
    if player:
        player.balance_bonus += amount
        player.wagering_requirement += target
        player.wagering_remaining += target
        session.add(player)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        tenant_id=campaign.tenant_id,
        action="BONUS_GRANT",
        resource_type="bonus_grant",
        resource_id=grant.id,
        result="success",
        reason=reason,
        details={"amount": amount, "player_id": player_id}
    )
    await session.commit()
    await session.refresh(grant)
    return grant

@router.get("/player/{player_id}")
async def list_player_bonuses(
    player_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(BonusGrant).where(BonusGrant.player_id == player_id).order_by(BonusGrant.granted_at.desc())
    return (await session.execute(stmt)).scalars().all()
