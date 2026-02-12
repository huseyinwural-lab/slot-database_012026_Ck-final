from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Dict, Any, List
from datetime import datetime, timedelta
from datetime import datetime

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.risk import RiskProfile, RiskLevel
from app.models.risk_history import RiskHistory
from app.utils.auth import get_current_admin
from app.services.risk_service import RiskService
from app.core.redis_client import get_redis

router = APIRouter(prefix="/api/v1/admin/risk", tags=["risk_admin"])

@router.get("/{user_id}/profile")
async def get_risk_profile(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(RiskProfile).where(RiskProfile.user_id == user_id)
    profile = (await session.execute(stmt)).scalars().first()
    
    if not profile:
        return {"status": "NO_PROFILE", "risk_score": 0, "risk_level": "LOW"}
        
    return profile

@router.get("/{user_id}/history")
async def get_risk_history(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(RiskHistory).where(RiskHistory.user_id == user_id).order_by(RiskHistory.created_at.desc()).limit(50)
    history = (await session.execute(stmt)).scalars().all()
    return history

@router.post("/{user_id}/override")
async def override_risk_score(
    user_id: str,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Manual override of risk score.
    Payload: { "score": 50, "reason": "Investigation result" }
    """
    new_score = payload.get("score")
    expiry_hours = payload.get("expiry_hours")
    
    expires_at = None
    if expiry_hours:
        expires_at = datetime.utcnow() + timedelta(hours=int(expiry_hours))
    reason = payload.get("reason")
    
    if new_score is None or not (0 <= new_score <= 100):
        raise HTTPException(status_code=400, detail="Invalid score")
    
    redis = await get_redis()
    service = RiskService(session, redis)
    
    # 1. Get/Create Profile
    stmt = select(RiskProfile).where(RiskProfile.user_id == user_id)
    profile = (await session.execute(stmt)).scalars().first()
    
    if not profile:
        # Create blank if forcing risk on new user
        profile = RiskProfile(user_id=user_id, tenant_id=current_admin.tenant_id, risk_score=0)
        session.add(profile)
        await session.flush()
        
    old_score = profile.risk_score
    old_level = profile.risk_level
    
    profile.risk_score = new_score
    profile.risk_level = service._map_score_to_level(new_score)
    profile.last_event_at = datetime.utcnow()
    if expires_at:
        profile.override_expires_at = expires_at
        profile.flags["override_active"] = True
    
    history = RiskHistory(
        user_id=profile.user_id,
        tenant_id=profile.tenant_id,
        old_score=old_score,
        new_score=profile.risk_score,
        old_level=old_level,
        new_level=profile.risk_level,
        change_reason=f"Manual Override: {reason}",
        changed_by=str(current_admin.id)
    )
    
    session.add(profile)
    session.add(history)
    await session.commit()
    
    return {"status": "updated", "profile": profile}
