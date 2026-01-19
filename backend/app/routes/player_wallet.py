from fastapi import APIRouter, Depends, HTTPException, Body, Header, Request
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from decimal import Decimal

from app.models.sql_models import Transaction, Player
from app.core.database import get_session
from app.utils.auth_player import get_current_player
from app.models.common import PaginatedResponse
from app.core.errors import AppError
from app.services.audit import audit
from app.models.wallet import WalletTxResponse
from config import settings
from app.services.ledger_shadow import shadow_append_event, shadow_apply_delta
from app.repositories.ledger_repo import get_balance
from app.services import ledger_telemetry

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
async def get_player_balance(
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

    # Tenant daily deposit limit enforcement (TENANT-POLICY-001)
    from app.services.tenant_policy_enforcement import ensure_within_tenant_daily_limits

    # New: Velocity Check (1 min window)
    from app.services.tenant_policy_enforcement import check_velocity_limit
    await check_velocity_limit(session, player_id=current_player.id, action="deposit")


    tenant_id = current_player.tenant_id
    try:
        await ensure_within_tenant_daily_limits(
            session,
            tenant_id=tenant_id,
            player_id=current_player.id,
            action="deposit",
            amount=amount,
            currency="USD",
        )
    except HTTPException as e:
        if e.status_code == 422 and isinstance(e.detail, dict) and e.detail.get("error_code") == "LIMIT_EXCEEDED":
            request_id = request.headers.get("X-Request-Id", "unknown")
            ip = request.client.host if request.client else None
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=current_player.id,
                tenant_id=tenant_id,
                action="FIN_TENANT_LIMIT_BLOCKED",
                resource_type="wallet_transaction",
                resource_id=current_player.id,
                result="failure",
                details=e.detail,
                ip_address=ip,
            )
            await session.commit()
        raise e

    # Test-only payment method gate: allow "test" only in dev/local/test or when flag enabled
    env = (settings.env or "").lower()
    is_test_mode = settings.allow_test_payment_methods or env in {"dev", "local", "test", "ci"}
    if method == "test" and not is_test_mode:
        raise HTTPException(status_code=400, detail={"error_code": "PAYMENT_METHOD_NOT_ALLOWED"})

    await session.refresh(current_player)

    # Compute request hash for conflict detection
    body = {"amount": amount, "method": method}
    req_hash = _compute_request_hash("POST", "/api/v1/player/wallet/deposit", body)

    # Optional test hook (dev/local/test): force deterministic PSP outcome
    mock_outcome_body = (request.json.get("mock_outcome") if hasattr(request, "json") else None)

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
        # DB stores TIMESTAMP WITHOUT TIME ZONE, so keep comparisons naive UTC.
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        start = datetime(year=now.year, month=now.month, day=now.day)
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
    session.add(tx)
    await session.flush()

    from app.services.transaction_state_machine import (
        STATE_PENDING_PROVIDER,
        STATE_COMPLETED,
        transition_transaction,
    )

    # --- State machine: created -> pending_provider -> completed ---
    old_state = tx.state
    transition_transaction(tx, STATE_PENDING_PROVIDER)

    # Audit: deposit moved to pending_provider
    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=current_player.id,
        tenant_id=current_player.tenant_id,
        action="FIN_DEPOSIT_PENDING_PROVIDER",
        resource_type="wallet_deposit",
        resource_id=tx.id,
        result="success",
        details={
            "tx_id": tx.id,
            "player_id": current_player.id,
            "amount": amount,
            "idempotency_key": idempotency_key,
            "old_state": old_state,
            "new_state": tx.state,
        },
        ip_address=ip,
    )

    # Finalise to completed
    old_state = tx.state
    transition_transaction(tx, STATE_COMPLETED)

    # Audit: deposit completed (logical success). Actual wallet/ledger delta
    # will only be applied after PSP capture confirms success.
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
            "old_state": old_state,
            "new_state": tx.state,
        },
        ip_address=ip,
    )

    # PSP integration (MockPSP) is still called for side-effects and provider
    # references, but no longer drives balance changes directly; those are
    # handled exclusively via the wallet+ledger service above.
    from app.services.psp import get_psp
    from app.services.psp.psp_interface import build_psp_idem_key

    psp = get_psp()
    psp_idem_key = build_psp_idem_key(str(tx.id))

    # In dev/test, allow tests to force a deterministic PSP outcome via header.
    mock_outcome = (request.headers.get("X-Mock-Outcome") or "").strip()
    if mock_outcome and hasattr(psp, "register_outcome_override"):
        try:
            psp.register_outcome_override(psp_idem_key, mock_outcome)
        except TypeError:
            # Real PSP implementations won't expose this hook.
            pass

    # Authorize step (no balance delta)
    await psp.authorize_deposit(
        tx_id=str(tx.id),
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        amount=float(amount),
        currency=tx.currency or "USD",
        psp_idem_key=psp_idem_key,
    )

    # Capture step: only on PSP success do we apply the wallet+ledger delta.
    psp_cap = await psp.capture_deposit(
        tx_id=str(tx.id),
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        amount=float(amount),
        currency=tx.currency or "USD",
        psp_idem_key=psp_idem_key,
    )

    from app.services.wallet_ledger import apply_wallet_delta_with_ledger
    from app.services.psp.psp_interface import PSPStatus

    if psp_cap.status == PSPStatus.CAPTURED:
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id=current_player.tenant_id,
            player_id=current_player.id,
            tx_id=str(tx.id),
            event_type="deposit_succeeded",
            delta_available=float(amount),
            delta_held=0.0,
            currency=tx.currency or "USD",
            idempotency_key=f"{psp_idem_key}:capture",
            provider=psp_cap.provider,
            provider_ref=psp_cap.provider_ref,
            provider_event_id=psp_cap.provider_event_id,
        )

    # Persist all changes (transaction, audit logs, wallet+ledger deltas)
    await session.commit()
    await session.refresh(tx)
    await session.refresh(current_player)

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
    # Velocity Check (Global Spam Protection)
    from app.services.tenant_policy_enforcement import check_velocity_limit
    await check_velocity_limit(session, player_id=current_player.id, action="withdraw")

    # Bonus Wagering Check
    from app.services.tenant_policy_enforcement import check_wagering_requirement
    await check_wagering_requirement(session, player_id=current_player.id)

    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"error_code": "IDEMPOTENCY_KEY_REQUIRED"})

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    idempotency_key = request.headers.get("Idempotency-Key")
    currency = "USD"  # TODO: support multi-currency when introduced

    # Tenant daily withdraw limit enforcement (TENANT-POLICY-001)
    from app.services.tenant_policy_enforcement import ensure_within_tenant_daily_limits

    tenant_id = current_player.tenant_id
    try:
        await ensure_within_tenant_daily_limits(
            session,
            tenant_id=tenant_id,
            player_id=current_player.id,
            action="withdraw",
            amount=amount,
            currency=currency,
        )
    except HTTPException as e:
        if e.status_code == 422 and isinstance(e.detail, dict) and e.detail.get("error_code") == "LIMIT_EXCEEDED":
            request_id = request.headers.get("X-Request-Id", "unknown")
            ip = request.client.host if request.client else None
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=current_player.id,
                tenant_id=tenant_id,
                action="FIN_TENANT_LIMIT_BLOCKED",
                resource_type="wallet_transaction",
                resource_id=current_player.id,
                result="failure",
                details=e.detail,
                ip_address=ip,
            )
            await session.commit()
        raise e

    # Test-only withdraw method gate: allow "test_bank" only in dev/local/test or when flag enabled
    env = (settings.env or "").lower()
    is_test_mode = settings.allow_test_payment_methods or env in {"dev", "local", "test", "ci"}
    if method == "test_bank" and not is_test_mode:
        raise HTTPException(status_code=400, detail={"error_code": "WITHDRAW_METHOD_NOT_ALLOWED"})

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

    # Idempotency check (early-return BEFORE balance checks)
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

        # Replay: return same tx, no state/balance change and NO further funds checks
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

    # Ledger snapshot for enforce / telemetry
    ledger_wb = None
    if settings.ledger_enforce_balance or settings.ledger_balance_mismatch_log:
        # When enforcement is ON, take a row lock on the wallet snapshot to
        # reduce race windows on concurrent withdraws. Telemetry-only reads
        # (enforce OFF) stay lock-free.
        ledger_wb = await get_balance(
            session,
            tenant_id=current_player.tenant_id,
            player_id=current_player.id,
            currency=currency,
            lock_for_update=bool(settings.ledger_enforce_balance),
        )

    # Telemetry: always record mismatch when enabled
    if settings.ledger_balance_mismatch_log and ledger_wb is not None:
        if ledger_wb.balance_real_available != current_player.balance_real_available:
            ledger_telemetry.record_balance_mismatch(
                tenant_id=current_player.tenant_id,
                player_id=current_player.id,
                currency=currency,
                player_available=current_player.balance_real_available,
                ledger_available=ledger_wb.balance_real_available,
            )

    # Funds check
    if settings.ledger_enforce_balance:
        if ledger_wb.balance_real_available < amount:
            raise HTTPException(status_code=400, detail={"error_code": "INSUFFICIENT_FUNDS"})
    else:
        if current_player.balance_real_available < amount:
            raise HTTPException(status_code=400, detail={"error_code": "INSUFFICIENT_FUNDS"})

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
        idempotency_key=idempotency_key,
        metadata_json={"request_hash": req_hash, "address": address},
        balance_after=(before_available - amount) + before_held,
    )

    session.add(tx)

    # Apply hold move via canonical wallet+ledger service
    from app.services.wallet_ledger import apply_wallet_delta_with_ledger

    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        tx_id=tx_id,
        event_type="withdraw_requested",
        delta_available=-float(amount),
        delta_held=+float(amount),
        currency=currency,
        idempotency_key=idempotency_key,
    )

    # Audit withdraw requested (idempotent on our side; API level idem zaten yukarıda)
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
