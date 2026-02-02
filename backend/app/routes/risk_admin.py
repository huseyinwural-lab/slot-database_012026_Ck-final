from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.poker_mtt_models import RiskSignal
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.poker_risk_engine import PokerRiskEngine

router = APIRouter(prefix="/api/v1/admin/risk", tags=["risk_admin"])

@router.get("/signals", response_model=List[RiskSignal])
async def list_risk_signals(
    request: Request,
    type: str = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    stmt = select(RiskSignal).where(RiskSignal.tenant_id == tenant_id)
    if type:
        stmt = stmt.where(RiskSignal.signal_type == type)
    stmt = stmt.order_by(RiskSignal.created_at.desc())
    return (await session.execute(stmt)).scalars().all()

@router.post("/players/{player_id}/flag")
async def flag_player(
    player_id: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    engine = PokerRiskEngine()
    signal = await engine.report_signal(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        signal_type="MANUAL_FLAG",
        severity="high",
        payload={"reason": payload.get("reason"), "admin": current_admin.email}
    )
    await session.commit()
    return signal
