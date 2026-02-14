from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.dispute_models import Dispute
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.dispute_engine import DisputeEngine

router = APIRouter(prefix="/api/v1/admin/disputes", tags=["disputes"])

@router.get("", response_model=List[Dispute])
async def list_disputes(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    stmt = select(Dispute).where(Dispute.tenant_id == tenant_id).order_by(Dispute.created_at.desc())
    return (await session.execute(stmt)).scalars().all()

@router.post("")
async def create_manual_dispute(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    engine = DisputeEngine()
    try:
        dispute = await engine.create_dispute(
            session, 
            tenant_id, 
            payload["transaction_id"], 
            payload.get("reason", "manual_entry")
        )
        await session.commit()
        await session.refresh(dispute)
        return dispute
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    decision = payload["decision"] # WON, LOST
    note = payload.get("note")
    
    engine = DisputeEngine()
    try:
        dispute = await engine.resolve_dispute(session, dispute_id, decision, note)
        await session.commit()
        await session.refresh(dispute)
        return dispute
    except ValueError as e:
        raise HTTPException(400, str(e))
