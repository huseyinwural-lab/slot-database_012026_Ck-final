from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.risk_history import RiskHistory
from app.models.risk import RiskProfile, RiskLevel
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/risk", tags=["risk_dashboard"])

@router.get("/dashboard")
async def get_risk_dashboard(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(None, current_admin, session)
    
    # Aggregates
    # High Risk Players
    count_high = (await session.execute(
        select(func.count()).where(RiskProfile.risk_level == RiskLevel.HIGH, RiskProfile.tenant_id == tenant_id)
    )).scalar() or 0
    
    # Daily Alerts (Risk History count today)
    # Simplified to total history count for now to avoid date math import overhead if not needed strictly
    count_alerts = (await session.execute(
        select(func.count()).where(RiskHistory.tenant_id == tenant_id)
    )).scalar() or 0

    return {
        "daily_alerts": count_alerts,
        "open_cases": 0, # Stub
        "bonus_abuse_alerts": 0, # Stub
        "high_risk_players": count_high
    }

@router.get("/rules")
async def get_risk_rules(current_admin: AdminUser = Depends(get_current_admin)):
    # Return hardcoded rules from V2 engine or empty
    return [
        {"id": "1", "name": "Rapid Deposit", "category": "payment", "score_impact": 30, "status": "active"},
        {"id": "2", "name": "Rapid Withdraw", "category": "payment", "score_impact": 20, "status": "active"},
        {"id": "3", "name": "High Velocity Bet", "category": "game", "score_impact": 10, "status": "active"},
    ]

# Stubs for other UI tabs
@router.get("/velocity")
async def get_velocity(current_admin: AdminUser = Depends(get_current_admin)):
    return []

@router.get("/blacklist")
async def get_blacklist(current_admin: AdminUser = Depends(get_current_admin)):
    return []

@router.post("/blacklist")
async def add_blacklist(payload: Dict = Body(...), current_admin: AdminUser = Depends(get_current_admin)):
    return {"status": "ok"}

@router.get("/cases")
async def get_cases(current_admin: AdminUser = Depends(get_current_admin)):
    return []

@router.get("/alerts")
async def get_alerts(current_admin: AdminUser = Depends(get_current_admin)):
    return []

@router.get("/evidence")
async def get_evidence(current_admin: AdminUser = Depends(get_current_admin)):
    return []
