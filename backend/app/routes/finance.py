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
    player_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,

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

    if player_id:
        query = query.where(Transaction.player_id == player_id)

    if date_from:
        query = query.where(Transaction.created_at >= date_from)
    if date_to:
        query = query.where(Transaction.created_at <= date_to)

    query = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()

    # Simple offset pagination meta
    count_query = select(func.count()).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    if state:
        count_query = count_query.where(Transaction.state == state)
    if player_id:
        count_query = count_query.where(Transaction.player_id == player_id)
    if date_from:
        count_query = count_query.where(Transaction.created_at >= date_from)
    if date_to:
        count_query = count_query.where(Transaction.created_at <= date_to)

    total = (await session.execute(count_query)).scalar() or 0

    return {
        "items": [
            {
                "tx_id": tx.id,
                "player_id": tx.player_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "state": tx.state,
                "status": tx.status,
                "created_at": tx.created_at,
                "reviewed_by": tx.reviewed_by,
                "reviewed_at": tx.reviewed_at,
                "balance_after": tx.balance_after,
            }
            for tx in items
        ],
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }



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
