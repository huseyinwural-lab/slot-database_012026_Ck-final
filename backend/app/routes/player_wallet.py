from fastapi import APIRouter, Depends, HTTPException, Body, Header
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.sql_models import Transaction, Player
from app.core.database import get_session
from app.utils.auth_player import get_current_player
from app.models.common import PaginatedResponse
from app.core.errors import AppError
from app.services.audit import audit
from config import settings

router = APIRouter(prefix="/api/v1/player/wallet", tags=["player_wallet"])


def _compute_request_hash(method: str, path: str, body: dict) -> str:
    payload = {
        "method": method,
        "path": path,
        "body": body or {},
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@router.get("/balance")
async def get_balance(
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    """Get current player balance"""
    await session.refresh(current_player)
    total_real = (current_player.balance_real_available or 0) + (current_player.balance_real_held or 0)
    return {
        "available_real": current_player.balance_real_available,
        "held_real": current_player.balance_real_held,
        "total_real": total_real,
    }


@router.post("/deposit")
async def create_deposit(
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    if not idempotency_key:
        raise AppError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required", status_code=400)

    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    await session.refresh(current_player)

    # Compute request hash for conflict detection
    req_hash = _compute_request_hash("POST", "/api/v1/player/wallet/deposit", {"amount": amount, "method": method})

    # Check existing transaction by idempotency key
    stmt = select(Transaction).where(
        Transaction.player_id == current_player.id,
        Transaction.idempotency_key == idempotency_key,
        Transaction.type == "deposit",
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        meta = existing.metadata_json or {}
        existing_hash = meta.get("request_hash")
        if existing_hash and existing_hash != req_hash:
            raise AppError(
                "IDEMPOTENCY_KEY_REUSE_CONFLICT",
                "Idempotency key reused with different payload",
                status_code=409,
            )
        # Idempotent replay
        raise AppError(
            "FIN_IDEMPOTENCY_HIT",
            "Idempotent replay",
            status_code=200,
            details={"transaction_id": existing.id},
        )

    tx_id = str(uuid.uuid4())

    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="deposit",
        amount=amount,
        status="completed",
        state="created",
        method=method,
        provider_tx_id="MockGateway",
        idempotency_key=idempotency_key,
        metadata_json={"request_hash": req_hash},
        balance_after=current_player.balance_real_available + amount,
    )

    # Simulated state machine: created -> pending_provider -> completed
    tx.state = "pending_provider"
    # ... here a real provider integration would be called ...
    tx.state = "completed"

    # Update Player Balance only on completed
    current_player.balance_real_available += amount

    session.add(tx)
    session.add(current_player)

    await session.commit()
    await session.refresh(tx)

    total_real = current_player.balance_real_available + current_player.balance_real_held
    return {
        "transaction": tx,
        "balance": {
            "available_real": current_player.balance_real_available,
            "held_real": current_player.balance_real_held,
            "total_real": total_real,
        },
    }


@router.post("/withdraw")
async def create_withdrawal(
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    address: str = Body(..., embed=True),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    if not idempotency_key:
        raise AppError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required", status_code=400)

    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    await session.refresh(current_player)

    # KYC gate
    if current_player.kyc_status != "verified":
        raise AppError("KYC_REQUIRED_FOR_WITHDRAWAL", "KYC verification required for withdrawal", status_code=403)

    # Balance check on available only
    if current_player.balance_real_available < amount:
        raise HTTPException(400, "Insufficient funds")

    # Idempotency check
    req_hash = _compute_request_hash("POST", "/api/v1/player/wallet/withdraw", {"amount": amount, "method": method, "address": address})
    stmt = select(Transaction).where(
        Transaction.player_id == current_player.id,
        Transaction.idempotency_key == idempotency_key,
        Transaction.type == "withdrawal",
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        meta = existing.metadata_json or {}
        existing_hash = meta.get("request_hash")
        if existing_hash and existing_hash != req_hash:
            raise AppError(
                "IDEMPOTENCY_KEY_REUSE_CONFLICT",
                "Idempotency key reused with different payload",
                status_code=409,
            )
        raise AppError(
            "FIN_IDEMPOTENCY_HIT",
            "Idempotent replay",
            status_code=200,
            details={"transaction_id": existing.id},
        )

    tx_id = str(uuid.uuid4())

    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="withdrawal",
        amount=amount,
        status="pending",
        state="requested",
        method=method,
        metadata_json={"request_hash": req_hash, "address": address},
        balance_after=(current_player.balance_real_available - amount) + current_player.balance_real_held,
    )

    # Hold accounting: move from available to held
    current_player.balance_real_available -= amount
    current_player.balance_real_held += amount

    session.add(tx)
    session.add(current_player)

    await session.commit()
    await session.refresh(tx)

    total_real = current_player.balance_real_available + current_player.balance_real_held
    return {
        "transaction": tx,
        "balance": {
            "available_real": current_player.balance_real_available,
            "held_real": current_player.balance_real_held,
            "total_real": total_real,
        },
    }


@router.get("/transactions", response_model=dict)
async def get_my_transactions(
    current_player: Player = Depends(get_current_player),
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_session)
):
    skip = (page - 1) * limit

    query = select(Transaction).where(Transaction.player_id == current_player.id).order_by(Transaction.created_at.desc())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "meta": {"total": total, "page": page, "page_size": limit},
    }
