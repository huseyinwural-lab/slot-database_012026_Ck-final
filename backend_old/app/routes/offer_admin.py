from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.offer_models import Offer, Experiment
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.offer_engine import OfferEngine

router = APIRouter(prefix="/api/v1/offers", tags=["offers"])

@router.post("")
async def create_offer(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    offer = Offer(
        tenant_id=tenant_id,
        name=payload["name"],
        type=payload["type"],
        cost_model=payload.get("cost_model", "fixed"),
        cost_value=float(payload.get("cost_value", 0)),
        config=payload.get("config", {})
    )
    session.add(offer)
    await session.commit()
    await session.refresh(offer)
    return offer

@router.post("/experiments")
async def create_experiment(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    exp = Experiment(
        tenant_id=tenant_id,
        key=payload["key"],
        name=payload["name"],
        status=payload.get("status", "draft"),
        variants=payload.get("variants", {})
    )
    session.add(exp)
    await session.commit()
    await session.refresh(exp)
    return exp

@router.post("/evaluate")
async def evaluate_trigger(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Admin debug: Simulate Trigger"""
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    engine = OfferEngine()
    record = await engine.evaluate_trigger(
        session, 
        tenant_id, 
        payload["player_id"], 
        payload["trigger_event"]
    )
    await session.commit()
    await session.refresh(record)
    return record
