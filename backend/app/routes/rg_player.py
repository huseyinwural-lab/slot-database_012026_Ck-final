from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.sql_models import Player
from app.utils.auth_player import get_current_player
from app.services.audit import audit
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
    
    return {"status": "excluded", "period_days": period_days}
