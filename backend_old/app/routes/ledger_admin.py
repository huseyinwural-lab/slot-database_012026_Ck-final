from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.sql_models import AdminUser, Player
from app.repositories.ledger_repo import get_balance
from app.utils.auth import get_current_admin
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.utils.tenant import get_current_tenant_id


router = APIRouter(prefix="/api/v1/admin", tags=["admin_ledger"])


@router.get("/players/{player_id}/wallet")
async def admin_get_player_wallet(
    player_id: str,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Player).where(Player.id == player_id, Player.tenant_id == tenant_id)
    player = (await session.execute(stmt)).scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    available = float(player.balance_real_available or 0.0)
    held = float(player.balance_real_held or 0.0)

    return {
        "player_id": player.id,
        "tenant_id": player.tenant_id,
        "currency": "USD",
        "wallet": {
            "available_real": available,
            "held_real": held,
            "total_real": available + held,
        },
    }


@router.get("/players/{player_id}/ledger/balance")
async def admin_get_player_ledger_balance(
    player_id: str,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # Ensure player exists in tenant (tenant boundary = 404)
    stmt = select(Player.id).where(Player.id == player_id, Player.tenant_id == tenant_id)
    exists = (await session.execute(stmt)).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Player not found")

    bal = await get_balance(session, tenant_id=tenant_id, player_id=player_id, currency="USD")
    available = float(bal.balance_real_available or 0.0)
    pending = float(bal.balance_real_pending or 0.0)

    return {
        "player_id": player_id,
        "tenant_id": tenant_id,
        "currency": "USD",
        "ledger": {
            "available_real": available,
            "pending_real": pending,
            "total_real": available + pending,
            "updated_at": getattr(bal, "updated_at", None),
        },
    }


@router.post("/ledger/adjust")
async def admin_ledger_adjust(
    request: Request,
    player_id: str = Body(...),
    delta: float = Body(...),
    reason: str = Body(...),
    currency: str = Body("USD"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"error_code": "IDEMPOTENCY_KEY_REQUIRED"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # Tenant boundary: require player in same tenant
    stmt = select(Player.id).where(Player.id == player_id, Player.tenant_id == tenant_id)
    exists = (await session.execute(stmt)).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Player not found")

    tx_id = str(uuid.uuid4())

    created = await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=player_id,
        tx_id=tx_id,
        event_type="manual_adjust",
        delta_available=float(delta),
        delta_held=0.0,
        currency=currency,
        idempotency_key=idempotency_key,
        provider="admin",
        provider_ref=reason,
        provider_event_id=f"admin_adjust:{idempotency_key}",
    )

    await session.commit()

    # Snapshots after operation
    stmt_p = select(Player).where(Player.id == player_id, Player.tenant_id == tenant_id)
    player = (await session.execute(stmt_p)).scalars().first()
    bal = await get_balance(session, tenant_id=tenant_id, player_id=player_id, currency=currency)

    wallet_available = float(player.balance_real_available or 0.0) if player else 0.0
    wallet_held = float(player.balance_real_held or 0.0) if player else 0.0
    ledger_available = float(bal.balance_real_available or 0.0)
    ledger_pending = float(bal.balance_real_pending or 0.0)

    return {
        "status": "ok",
        "idempotent_replay": not created,
        "idempotency_key": idempotency_key,
        "tx_id": tx_id,
        "at": datetime.utcnow().isoformat(),
        "wallet": {
            "available_real": wallet_available,
            "held_real": wallet_held,
            "total_real": wallet_available + wallet_held,
        },
        "ledger": {
            "available_real": ledger_available,
            "pending_real": ledger_pending,
            "total_real": ledger_available + ledger_pending,
        },
    }
