from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from app.core.database import get_session
from app.models.sql_models import AdminUser, Player
from app.models.vip_models import VipTier
from app.services.vip_engine import VipEngine
from app.utils.auth import get_current_admin
from app.utils.auth_player import get_current_player
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/vip", tags=["vip"])

# --- ADMIN ---

@router.get("/tiers", response_model=List[VipTier])
async def list_tiers(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    stmt = select(VipTier).where(VipTier.tenant_id == tenant_id).order_by(VipTier.min_points.asc())
    return (await session.execute(stmt)).scalars().all()

@router.post("/tiers")
async def create_tier(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    tier = VipTier(
        tenant_id=tenant_id,
        name=payload["name"],
        min_points=float(payload.get("min_points", 0)),
        cashback_percent=float(payload.get("cashback_percent", 0)),
        rakeback_percent=float(payload.get("rakeback_percent", 0)),
        config=payload.get("config", {})
    )
    session.add(tier)
    await session.commit()
    await session.refresh(tier)
    return tier

@router.post("/simulate")
async def simulate_activity(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Debug: Award points manually."""
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player_id = payload["player_id"]
    points = float(payload["points"])
    
    engine = VipEngine()
    await engine.award_points(
        session, 
        player_id=player_id, 
        tenant_id=tenant_id, 
        points=points, 
        source_type="MANUAL_SIM", 
        source_ref="admin_manual"
    )
    await session.commit()
    return {"status": "ok", "awarded": points}

# --- PLAYER ---

@router.get("/me")
async def get_my_vip_status(
    request: Request,
    session: AsyncSession = Depends(get_session),
    player: Player = Depends(get_current_player)
):
    engine = VipEngine()
    status = await engine.get_status(session, player.id, player.tenant_id)
    
    # Enrich with Tier Name
    tier_name = "None"
    if status.current_tier_id:
        tier = await session.get(VipTier, status.current_tier_id)
        if tier:
            tier_name = tier.name
            
    return {
        "status": status,
        "tier_name": tier_name
    }

@router.post("/redeem")
async def redeem_points(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    player: Player = Depends(get_current_player)
):
    points = float(payload.get("points", 0))
    if points <= 0:
        raise HTTPException(400, "Points must be positive")
        
    engine = VipEngine()
    try:
        cash = await engine.redeem_points(session, player.id, points)
        await session.commit()
        return {"message": "Redeemed", "cash_received": cash}
    except ValueError as e:
        raise HTTPException(400, str(e))
