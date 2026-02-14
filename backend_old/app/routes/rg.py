from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from app.core.database import get_session
from app.models.sql_models import AdminUser, Player
from app.models.rg_models import PlayerRGProfile
from app.utils.auth import get_current_admin
from app.utils.auth_player import get_current_player
from app.services.audit import audit
from app.utils.reason import require_reason

router = APIRouter(prefix="/api/v1/rg", tags=["rg"])

# --- PLAYER RG API ---

@router.post("/limits")
async def set_rg_limits(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    # Only player sets their own limits (or reduce them immediately). 
    # Increasing limits usually requires cooldown (not implemented in MVP).
    
    stmt = select(PlayerRGProfile).where(PlayerRGProfile.player_id == current_player.id)
    profile = (await session.execute(stmt)).scalars().first()
    
    if not profile:
        profile = PlayerRGProfile(tenant_id=current_player.tenant_id, player_id=current_player.id)
        session.add(profile)
        
    # Update fields
    for field in ["deposit_limit_daily", "deposit_limit_weekly", "deposit_limit_monthly", 
                  "loss_limit_daily", "loss_limit_weekly", "session_time_limit_minutes"]:
        if field in payload:
            setattr(profile, field, payload[field])
            
    profile.updated_at = datetime.now(timezone.utc)
    session.add(profile)
    
    # Audit (Player Action)
    # We log this even if player triggered, or maybe use separate audit for player actions?
    # Using unified audit table but with actor=player_id? Or system?
    # For now, let's skip deep audit for player-initiated actions unless critical (self-exclusion).
    # Or insert system event.
    
    await session.commit()
    return profile

@router.post("/self-exclude")
async def self_exclude(
    request: Request,
    payload: Dict[str, Any] = Body(...), # {duration_hours: int, permanent: bool}
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(PlayerRGProfile).where(PlayerRGProfile.player_id == current_player.id)
    profile = (await session.execute(stmt)).scalars().first()
    if not profile:
        profile = PlayerRGProfile(tenant_id=current_player.tenant_id, player_id=current_player.id)
        
    duration = payload.get("duration_hours")
    permanent = payload.get("permanent", False)
    
    if permanent:
        profile.self_excluded_permanent = True
        profile.self_excluded_until = datetime.max.replace(tzinfo=timezone.utc)
    elif duration:
        profile.self_excluded_until = datetime.now(timezone.utc) + timedelta(hours=duration)
    else:
        raise HTTPException(400, "Duration or permanent required")
        
    session.add(profile)
    
    # Update Player Status
    current_player.status = "self_excluded"
    session.add(current_player)
    
    # Audit (Critical)
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_player.id, # Player is actor
        actor_role="player",
        tenant_id=current_player.tenant_id,
        action="PLAYER_SELF_EXCLUDE",
        resource_type="player",
        resource_id=current_player.id,
        result="success",
        reason="Player Request",
        details={"permanent": permanent, "duration": duration}
    )
    
    await session.commit()
    return {"status": "excluded", "until": profile.self_excluded_until}

# --- ADMIN OVERRIDES ---

@router.post("/admin/override/{player_id}")
async def admin_override_rg(
    request: Request,
    player_id: str,
    payload: Dict[str, Any] = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(PlayerRGProfile).where(PlayerRGProfile.player_id == player_id)
    profile = (await session.execute(stmt)).scalars().first()
    if not profile:
        raise HTTPException(404, "Profile not found")
        
    # Apply changes (e.g. lift exclusion - risky!)
    if "lift_exclusion" in payload and payload["lift_exclusion"]:
        profile.self_excluded_until = None
        profile.self_excluded_permanent = False
        
        player = await session.get(Player, player_id)
        if player:
            player.status = "active"
            session.add(player)
            
    session.add(profile)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=profile.tenant_id,
        action="RG_ADMIN_OVERRIDE",
        resource_type="rg_profile",
        resource_id=player_id,
        result="success",
        reason=reason,
        details=payload
    )
    await session.commit()
    return profile
