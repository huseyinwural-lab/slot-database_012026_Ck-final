from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Dict, Any, List
import uuid

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.game_models import Game
from app.models.engine_models import EngineStandardProfile
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.audit import audit
from app.utils.reason import require_reason

router = APIRouter(prefix="/api/v1/engine", tags=["engine"])

# --- SEED DATA ---
STANDARD_PROFILES = [
    {
        "code": "slot.standard.low_risk.v1",
        "name": "Low Volatility (Entertainment)",
        "description": "Frequent small wins, extended playtime. RTP 96.5%, Hit Freq 35%, Max Win 500x.",
        "config": {"rtp": 96.5, "volatility": "LOW", "hit_frequency": 35, "max_win_multiplier": 500, "base_lines": 10}
    },
    {
        "code": "slot.standard.balanced.v1",
        "name": "Balanced (Standard)",
        "description": "Industry standard. Good mix of churn and chase. RTP 96.0%, Hit Freq 25%, Max Win 2500x.",
        "config": {"rtp": 96.0, "volatility": "MEDIUM", "hit_frequency": 25, "max_win_multiplier": 2500, "base_lines": 20}
    },
    {
        "code": "slot.standard.high_vol.v1",
        "name": "High Volatility (Hardcore)",
        "description": "High risk, huge potential. RTP 95.5%, Hit Freq 15%, Max Win 10000x.",
        "config": {"rtp": 95.5, "volatility": "HIGH", "hit_frequency": 15, "max_win_multiplier": 10000, "base_lines": 20}
    }
]

@router.get("/standards", response_model=List[EngineStandardProfile])
async def list_engine_standards(
    game_type: str = "SLOT",
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Lazy Seed
    stmt = select(EngineStandardProfile)
    existing = (await session.execute(stmt)).scalars().all()
    
    if not existing:
        for p in STANDARD_PROFILES:
            profile = EngineStandardProfile(
                code=p["code"],
                name=p["name"],
                description=p["description"],
                config=p["config"],
                game_type="SLOT"
            )
            session.add(profile)
        await session.commit()
        existing = (await session.execute(stmt)).scalars().all()
        
    if game_type:
        return [e for e in existing if e.game_type == game_type]
    return existing

@router.get("/game/{game_id}/config")
async def get_game_engine_config(
    game_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    game = await session.get(Game, game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    if game.tenant_id != tenant_id and not current_admin.is_platform_owner:
        raise HTTPException(403, "Access denied")
        
    # Extract engine config from general configuration
    # Convention: game.configuration['engine'] holds the engine specific data
    # Structure: { mode: "STANDARD"|"CUSTOM", profile_code: str, params: dict }
    return game.configuration.get("engine", {
        "mode": "STANDARD", 
        "profile_code": "slot.standard.balanced.v1", 
        "params": {}
    })

def is_dangerous_change(new_config: dict) -> bool:
    """Detect parameters that require specialized review."""
    # Example Rules
    if new_config.get("rtp", 0) > 98.0: return True
    if new_config.get("max_win_multiplier", 0) > 50000: return True
    return False

@router.post("/game/{game_id}/config")
async def update_game_engine_config(
    request: Request,
    game_id: str,
    payload: Dict[str, Any] = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Update Engine Config.
    Payload: { mode: "STANDARD"|"CUSTOM", profile_code: str, custom_params: dict }
    """
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    game = await session.get(Game, game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    
    # 1. Resolve Effective Config
    mode = payload.get("mode", "STANDARD")
    profile_code = payload.get("profile_code")
    custom_params = payload.get("custom_params", {})
    
    effective_config = {}
    
    # Check Profile
    stmt = select(EngineStandardProfile).where(EngineStandardProfile.code == profile_code)
    profile = (await session.execute(stmt)).scalars().first()
    
    if not profile and mode == "STANDARD":
        raise HTTPException(400, "Profile not found for STANDARD mode")
        
    base_config = profile.config if profile else {}
    
    if mode == "STANDARD":
        effective_config = base_config.copy()
    else:
        # Custom: Merge base with overrides
        effective_config = base_config.copy()
        effective_config.update(custom_params)
        
    # 2. Safety Check
    review_required = False
    if is_dangerous_change(effective_config):
        review_required = True
        # In a real system, we might create an ApprovalRequest here and return pending status.
        # For this scope, we log it explicitly as REVIEW_REQUIRED in audit and maybe block 'activate' flag.
        # We will proceed but mark it.
        
    # 3. Update Game
    old_engine = game.configuration.get("engine", {})
    
    new_engine_state = {
        "mode": mode,
        "profile_code": profile_code,
        "params": effective_config,
        "review_status": "PENDING" if review_required else "APPROVED"
    }
    
    # Merge into game configuration
    current_conf = dict(game.configuration)
    current_conf["engine"] = new_engine_state
    # Update root RTP for easy access if present
    if "rtp" in effective_config:
        game.rtp = float(effective_config["rtp"])
        
    game.configuration = current_conf
    session.add(game)
    
    # 4. Audit
    action = "ENGINE_CONFIG_UPDATE"
    if review_required:
        action = "ENGINE_CONFIG_UPDATE_DANGEROUS"
        
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=tenant_id,
        action=action,
        resource_type="game",
        resource_id=game.id,
        result="success",
        status="REVIEW_REQUIRED" if review_required else "SUCCESS",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        before=old_engine,
        after=new_engine_state,
        details={"mode": mode, "profile": profile_code, "dangerous": review_required}
    )
    
    await session.commit()
    
    return {
        "message": "Engine config updated",
        "review_required": review_required,
        "effective_config": effective_config
    }
