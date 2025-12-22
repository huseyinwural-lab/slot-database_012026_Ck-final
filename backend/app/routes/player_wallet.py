from fastapi import APIRouter, Depends, HTTPException, Body, Header, Request
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
from app.models.wallet import WalletTxResponse
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


@router.post("/deposit", response_model=WalletTxResponse)
async def create_deposit(
    request: Request,
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"error_code": "IDEMPOTENCY_KEY_REQUIRED"})

    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    await session.refresh(current_player)

    # Compute request hash for conflict detection
    body = {"amount": amount, "method": method}
    req_hash = _compute_request_hash("POST", "/api/v1/player/wallet/deposit", body)

    # Check existing transaction by idempotency key
    stmt = select(Transaction).where(
        Transaction.player_id == current_player.id,
        Transaction.idempotency_key == idempotency_key,
        Transaction.type == "deposit",
    )
    existing = (await session.execute(stmt)).scalars().first()
    request_id = request.headers.get("X-Request-Id", "unknown")
    ip = request.client.host if request.client else None

    if existing:
        meta = existing.metadata_json or {}
        existing_hash = meta.get("request_hash")
        # 1a) Conflict: same key but different payload
        if existing_hash and existing_hash != req_hash:
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=current_player.id,
                tenant_id=current_player.tenant_id,
                action="FIN_IDEMPOTENCY_CONFLICT",
                resource_type="wallet_deposit",
                resource_id=existing.id,
                result="conflict",
                details={
                    "tx_id": existing.id,
                    "player_id": current_player.id,
                    "idempotency_key": idempotency_key,
                    "existing_request_hash": existing_hash,
                    "incoming_request_hash": req_hash,
                },
                ip_address=ip,
            )
            raise HTTPException(
                status_code=409,
                detail={"error_code": "IDEMPOTENCY_KEY_REUSE_CONFLICT", "tx_id": existing.id},
            )

        # 1b) Replay: normal success response with same transaction
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=current_player.id,
            tenant_id=current_player.tenant_id,
            action="FIN_IDEMPOTENCY_HIT",
            resource_type="wallet_deposit",
            resource_id=existing.id,
            result="success",
            details={
                "tx_id": existing.id,
                "player_id": current_player.id,
                "idempotency_key": idempotency_key,
                "state": existing.state,
            },
            ip_address=ip,
        )
        total_real = (current_player.balance_real_available or 0) + (current_player.balance_real_held or 0)
        return {
            "transaction": existing,
            "balance": {
                "available_real": current_player.balance_real_available,
                "held_real": current_player.balance_real_held,
                "total_real": total_real,
            },
        }

    # Daily cap for unverified players
    cap = float(settings.kyc_unverified_daily_deposit_cap)
    if current_player.kyc_status != "verified":
        # Calculate today's completed deposits
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        start = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        cap_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.player_id == current_player.id,
            Transaction.type == "deposit",
            Transaction.state == "completed",
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        current_total = (await session.execute(cap_stmt)).scalar_one() or 0.0
        if current_total + amount > cap:
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=current_player.id,
                tenant_id=current_player.tenant_id,
                action="FIN_KYC_DEPOSIT_LIMIT_BLOCK",
                resource_type="wallet_deposit",
                resource_id=None,
                result="blocked",
                details={
                    "tx_id": None,
                    "player_id": current_player.id,
                    "amount": amount,
                    "currency": "USD",
                    "old_state": None,
                    "new_state": None,
                    "idempotency_key": idempotency_key,
                    "request_id": request_id,
                    "balance_available_before": current_player.balance_real_available,
                    "balance_available_after": current_player.balance_real_available,
                    "balance_held_before": current_player.balance_real_held,
                    "balance_held_after": current_player.balance_real_held,
                },
                ip_address=ip,
            )
            raise HTTPException(
                status_code=403,
                detail={"error_code": "KYC_DEPOSIT_LIMIT"},
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
        metadata_json={"request_hash": req_hash, "method": method},
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

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=current_player.id,
        tenant_id=current_player.tenant_id,
        action="FIN_DEPOSIT_COMPLETED",
        resource_type="wallet_deposit",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": current_player.id,
            "amount": amount,
            "idempotency_key": idempotency_key,
        },
        ip_address=ip,
    )

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
    request: Request,
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    address: str = Body(..., embed=True),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"error_code": "IDEMPOTENCY_KEY_REQUIRED"})

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    await session.refresh(current_player)

    request_id = request.headers.get("X-Request-Id", "unknown")
    ip = request.client.host if request.client else None

    # KYC gate
    if current_player.kyc_status != "verified":
        # Blocked withdraw due to KYC
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=current_player.id,
            tenant_id=current_player.tenant_id,
            action="FIN_KYC_WITHDRAW_BLOCK",
            resource_type="wallet_withdraw",
            resource_id=None,
            result="blocked",
            details={
                "tx_id": None,
                "player_id": current_player.id,
                "amount": amount,
                "currency": "USD",
                "old_state": None,
                "new_state": None,
                "idempotency_key": idempotency_key,
                "request_id": request_id,
                "balance_available_before": current_player.balance_real_available,
                "balance_available_after": current_player.balance_real_available,
                "balance_held_before": current_player.balance_real_held,
                "balance_held_after": current_player.balance_real_held,
            },
            ip_address=ip,
        )
        raise HTTPException(
            status_code=403,
            detail={"error_code": "KYC_REQUIRED_FOR_WITHDRAWAL"},
        )

    # Balance check on available only
    if current_player.balance_real_available < amount:
        raise HTTPException(status_code=400, detail={"error_code": "INSUFFICIENT_FUNDS"})

    # Idempotency check
    body = {"amount": amount, "method": method, "address": address}
    req_hash = _compute_request_hash("POST", "/api/v1/player/wallet/withdraw", body)
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
            # Conflict
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=current_player.id,
                tenant_id=current_player.tenant_id,
                action="FIN_IDEMPOTENCY_CONFLICT",
                resource_type="wallet_withdraw",
                resource_id=existing.id,
                result="conflict",
                details={
                    "tx_id": existing.id,
                    "player_id": current_player.id,
                    "amount": existing.amount,
                    "currency": existing.currency,
                    "old_state": existing.state,
                    "new_state": existing.state,
                    "idempotency_key": idempotency_key,
                    "request_id": request_id,
                    "balance_available_before": current_player.balance_real_available,
                    "balance_available_after": current_player.balance_real_available,
                    "balance_held_before": current_player.balance_real_held,
                    "balance_held_after": current_player.balance_real_held,
                },
                ip_address=ip,
            )
            raise HTTPException(
                status_code=409,
                detail={"error_code": "IDEMPOTENCY_CONFLICT", "tx_id": existing.id},
            )

        # Replay: return same tx, no state/balance change
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=current_player.id,
            tenant_id=current_player.tenant_id,
            action="FIN_IDEMPOTENCY_HIT",
            resource_type="wallet_withdraw",
            resource_id=existing.id,
            result="success",
            details={
                "tx_id": existing.id,
                "player_id": current_player.id,
                "amount": existing.amount,
                "currency": existing.currency,
                "old_state": existing.state,
                "new_state": existing.state,
                "idempotency_key": idempotency_key,
                "request_id": request_id,
                "balance_available_before": current_player.balance_real_available,
                "balance_available_after": current_player.balance_real_available,
                "balance_held_before": current_player.balance_real_held,
                "balance_held_after": current_player.balance_real_held,
            },
            ip_address=ip,
        )
        total_real = (current_player.balance_real_available or 0) + (current_player.balance_real_held or 0)
        return {
            "transaction": existing,
            "balance": {
                "available_real": current_player.balance_real_available,
                "held_real": current_player.balance_real_held,
                "total_real": total_real,
            },
        }

    # New withdrawal
    before_available = current_player.balance_real_available
    before_held = current_player.balance_real_held

    tx_id = str(uuid.uuid4())

    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="withdrawal",
        amount=amount,
        currency="USD",
        status="pending",
        state="requested",
        method=method,
        metadata_json={"request_hash": req_hash, "address": address},
        balance_after=(before_available - amount) + before_held,
    )

    # Hold accounting: move from available to held
    current_player.balance_real_available = before_available - amount
    current_player.balance_real_held = before_held + amount

    session.add(tx)
    session.add(current_player)

    # Audit withdraw requested
    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=current_player.id,
        tenant_id=current_player.tenant_id,
        action="FIN_WITHDRAW_REQUESTED",
        resource_type="wallet_withdraw",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": current_player.id,
            "amount": amount,
            "currency": "USD",
            "old_state": "requested",
            "new_state": "requested",
            "idempotency_key": idempotency_key,
            "request_id": request_id,
            "balance_available_before": before_available,
            "balance_available_after": current_player.balance_real_available,
            "balance_held_before": before_held,
            "balance_held_after": current_player.balance_real_held,
        },
        ip_address=ip,
    )

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
