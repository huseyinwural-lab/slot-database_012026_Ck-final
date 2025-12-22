from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone


from app.core.errors import AppError
from app.models.sql_models import Transaction, Player
from app.services.audit import audit


from app.core.database import get_session
from app.models.sql_models import ReconciliationReport, ChargebackCase, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/finance", tags=["finance_advanced"])

@router.get("/withdrawals")
async def list_withdrawals(
    request: Request,
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    query = select(Transaction).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    if state:
        query = query.where(Transaction.state == state)

    query = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()



@router.get("/reconciliation")
async def get_reconciliations(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(ReconciliationReport).where(ReconciliationReport.tenant_id == tenant_id)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/chargebacks")
async def get_chargebacks(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(ChargebackCase).where(ChargebackCase.tenant_id == tenant_id)
    result = await session.execute(query)
    return result.scalars().all()
