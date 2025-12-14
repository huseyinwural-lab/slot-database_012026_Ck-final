from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import ReconciliationReport, ChargebackCase, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/finance", tags=["finance_advanced"])

@router.get("/reconciliation")
async def get_reconciliations(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(ReconciliationReport).where(ReconciliationReport.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    return result.scalars().all()

@router.get("/chargebacks")
async def get_chargebacks(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(ChargebackCase).where(ChargebackCase.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    return result.scalars().all()
