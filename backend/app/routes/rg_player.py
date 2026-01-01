from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.sql_models import Player
from app.utils.auth_player import get_current_player
from app.services.audit import audit
from app.models.rg_models import PlayerRGProfile
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/rg", tags=["responsible_gaming"])

@router.post("/self-exclude")
async def self_exclude(
    period_days: int = Body(..., embed=True),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    if period_days < 1:
        raise HTTPException(400, "Invalid period")
        
    # Logic: Set status to suspended and add note/time
    # In real world, we would have a dedicated 'exclusion_end_date' column.
    # For now, we use status='suspended' and metadata.
    
    current_player.status = "suspended"
    # Ideally store exclusion_end somewhere. Let's assume player model has metadata or we just rely on audit.
    # We will log it.
    
    await audit.log_event(
        session=session,
        request_id="self-exclusion",
        actor_user_id=current_player.id,
        tenant_id=current_player.tenant_id,
        action="RG_SELF_EXCLUSION",
        resource_type="player",
        resource_id=current_player.id,
        result="success",
        details={"period_days": period_days}
    )
    
    session.add(current_player)
    await session.commit()
    


@router.post("/player/exclusion")
async def set_player_exclusion(
    payload: dict = Body(...),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    """Player self-exclusion endpoint expected by policy_enforcement_test.

    Body example:
      {"type":"self_exclusion","duration_hours":24}
    """
    ex_type = payload.get("type")
    if ex_type != "self_exclusion":
        raise HTTPException(400, "Unsupported exclusion type")

    duration_hours = payload.get("duration_hours")
    try:
        duration_hours = int(duration_hours)
    except Exception:
        raise HTTPException(400, "Invalid duration_hours")

    if duration_hours < 1:
        raise HTTPException(400, "Invalid duration_hours")

    # Upsert RG profile
    from sqlmodel import select

    stmt = select(PlayerRGProfile).where(PlayerRGProfile.player_id == current_player.id)
    res = await session.execute(stmt)
    profile = res.scalars().first()
    if not profile:
        profile = PlayerRGProfile(tenant_id=current_player.tenant_id, player_id=current_player.id)

    profile.self_excluded_until = datetime.utcnow() + timedelta(hours=duration_hours)
    profile.self_excluded_permanent = False
    profile.updated_at = datetime.utcnow()

    session.add(profile)
    await session.commit()

    return {
        "status": "ok",
        "type": "self_exclusion",
        "duration_hours": duration_hours,
        "self_excluded_until": profile.self_excluded_until.isoformat(),
    }

    return {"status": "excluded", "period_days": period_days}
