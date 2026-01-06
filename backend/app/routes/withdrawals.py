from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.database import get_session
from app.models.sql_models import Transaction, Player, AdminUser
from app.services.audit import audit
from app.services.csv_export import dicts_to_csv_bytes
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/withdrawals", tags=["withdrawals"])


# External status values (UI contract) -> internal Transaction.state values
_STATUS_TO_STATES: Dict[str, List[str]] = {
    "pending": ["requested"],
    "approved": ["approved"],
    "processing": ["payout_pending"],
    "paid": ["paid"],
    "failed": ["payout_failed"],
    "rejected": ["rejected"],
}


def _normalize_status(status: Optional[str]) -> Optional[str]:
    if not status:
        return None
    s = status.strip().lower()
    if s in {"all", "*"}:
        return None
    return s


def _tx_state_to_status(state: Optional[str]) -> str:
    state = (state or "").strip().lower()
    if state == "requested":
        return "pending"
    if state == "approved":
        return "approved"
    if state == "payout_pending":
        return "processing"
    if state == "paid":
        return "paid"
    if state == "payout_failed":
        return "failed"
    if state == "rejected":
        return "rejected"
    return state or "unknown"


def _can_write(current_admin: AdminUser) -> bool:
    # P0: Ops/Admin can mutate. Support view-only.
    if getattr(current_admin, "is_platform_owner", False):
        return True

    tenant_role = (getattr(current_admin, "tenant_role", None) or "").strip().lower()
    if tenant_role in {"operations", "tenant_admin"}:
        return True
    if tenant_role in {"support"}:
        return False

    # Fallback to legacy role string
    role = (getattr(current_admin, "role", None) or "").strip().lower()
    if "support" in role:
        return False
    if "admin" in role or "ops" in role or "operation" in role:
        return True

    return False


def _require_write(current_admin: AdminUser) -> None:
    if not _can_write(current_admin):
        raise HTTPException(status_code=403, detail={"error_code": "FORBIDDEN"})


def _apply_filters(stmt, *, tenant_id: str, status: Optional[str], q: Optional[str], player_id: Optional[str], provider_ref: Optional[str]):
    stmt = stmt.where(Transaction.tenant_id == tenant_id, Transaction.type == "withdrawal")

    normalized = _normalize_status(status)
    if normalized:
        states = _STATUS_TO_STATES.get(normalized)
        if not states:
            # Unknown status -> empty result
            stmt = stmt.where(Transaction.id == "__nope__")
        else:
            stmt = stmt.where(Transaction.state.in_(states))

    if player_id:
        stmt = stmt.where(Transaction.player_id == player_id)

    # Free text search across tx id, player id, player username/email and provider refs
    if q:
        like = f"%{q.strip()}%"
        # Join-based filters are applied in the main query builder where Player is joined.
        # Here we only cover tx-scoped fields.
        stmt = stmt.where(
            (Transaction.id.ilike(like))
            | (Transaction.player_id.ilike(like))
            | (Transaction.provider_tx_id.ilike(like))
            | (Transaction.provider_event_id.ilike(like))
        )

    if provider_ref:
        like = f"%{provider_ref.strip()}%"
        stmt = stmt.where(
            (Transaction.provider_tx_id.ilike(like)) | (Transaction.provider_event_id.ilike(like))
        )

    return stmt


@router.get("")
async def list_withdrawals(
    request: Request,
    status: Optional[str] = None,
    q: Optional[str] = None,
    player_id: Optional[str] = None,
    provider_ref: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort: str = "created_at_desc",
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # Base stmt with join to Player for username/email search + KYC/Risk columns
    stmt = select(Transaction, Player).join(Player, Player.id == Transaction.player_id).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )

    stmt = _apply_filters(
        stmt,
        tenant_id=tenant_id,
        status=status,
        q=q,
        player_id=player_id,
        provider_ref=provider_ref,
    )

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Player.username.ilike(like)) | (Player.email.ilike(like)))

    # Sorting
    if sort == "created_at_asc":
        stmt = stmt.order_by(Transaction.created_at.asc())
    else:
        stmt = stmt.order_by(Transaction.created_at.desc())

    # Count
    count_stmt = select(func.count()).select_from(
        select(Transaction.id)
        .join(Player, Player.id == Transaction.player_id)
        .where(Transaction.tenant_id == tenant_id, Transaction.type == "withdrawal")
        .subquery()
    )

    # Apply same filters to count (without ordering/limit)
    # For simplicity and correctness in P0, re-run a count over the filtered ids.
    filtered_ids_stmt = select(Transaction.id).join(Player, Player.id == Transaction.player_id).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    filtered_ids_stmt = _apply_filters(
        filtered_ids_stmt,
        tenant_id=tenant_id,
        status=status,
        q=q,
        player_id=player_id,
        provider_ref=provider_ref,
    )
    if q:
        like = f"%{q.strip()}%"
        filtered_ids_stmt = filtered_ids_stmt.where((Player.username.ilike(like)) | (Player.email.ilike(like)))

    total = (await session.execute(select(func.count()).select_from(filtered_ids_stmt.subquery()))).scalar() or 0

    stmt = stmt.offset(offset).limit(limit)
    rows = (await session.execute(stmt)).all()

    items: List[Dict[str, Any]] = []
    for tx, player in rows:
        meta = tx.metadata_json or {}
        items.append(
            {
                "id": tx.id,
                "request_id": tx.id,
                "player_id": tx.player_id,
                "player_username": player.username,
                "player_email": player.email,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "status": _tx_state_to_status(tx.state),
                "state": tx.state,
                "method": tx.method,
                "destination": meta.get("address") or meta.get("destination") or None,
                "provider": tx.provider,
                "provider_ref": tx.provider_tx_id or tx.provider_event_id,
                "created_at": tx.created_at,
                "reviewed_by": tx.reviewed_by,
                "reviewed_at": tx.reviewed_at,
                "risk_score": player.risk_score,
                "kyc_status": player.kyc_status,
            }
        )

    return {"items": items, "meta": {"total": total, "limit": limit, "offset": offset}}


@router.post("/{withdrawal_id}/approve")
async def approve_withdrawal(
    withdrawal_id: str,
    request: Request,
    payload: Dict[str, Any] = Body(default={}),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    _require_write(current_admin)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Transaction).where(
        Transaction.id == withdrawal_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "WITHDRAWAL_NOT_FOUND"})

    # State-guard: approve only from pending
    if _tx_state_to_status(tx.state) != "pending":
        raise HTTPException(status_code=409, detail={"error_code": "INVALID_STATE_TRANSITION"})

    reason = (payload.get("reason") or "").strip() or None

    tx.state = "approved"
    tx.status = "approved"
    tx.review_reason = reason
    tx.reviewed_by = str(current_admin.id)
    tx.reviewed_at = datetime.utcnow()
    session.add(tx)

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="WITHDRAWAL_APPROVED",
        resource_type="withdrawal",
        resource_id=tx.id,
        result="success",
        details={"withdrawal_id": tx.id, "reason": reason},
        ip_address=ip,
    )

    await session.commit()
    await session.refresh(tx)

    return {"withdrawal": {"id": tx.id, "status": _tx_state_to_status(tx.state), "state": tx.state}}


@router.post("/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: str,
    request: Request,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    _require_write(current_admin)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    reason = (payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail={"error_code": "REASON_REQUIRED"})

    stmt = select(Transaction).where(
        Transaction.id == withdrawal_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "WITHDRAWAL_NOT_FOUND"})

    # State-guard: reject only from pending
    if _tx_state_to_status(tx.state) != "pending":
        raise HTTPException(status_code=409, detail={"error_code": "INVALID_STATE_TRANSITION"})

    tx.state = "rejected"
    tx.status = "rejected"
    tx.review_reason = reason
    tx.reviewed_by = str(current_admin.id)
    tx.reviewed_at = datetime.utcnow()

    # Release hold back to available (pending withdrawal holds funds)
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=tx.player_id,
        tx_id=str(tx.id),
        event_type="withdraw_rejected",
        delta_available=float(tx.amount),
        delta_held=-float(tx.amount),
        currency=tx.currency or "USD",
        idempotency_key=f"withdraw_reject:{tx.id}",
    )

    session.add(tx)

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="WITHDRAWAL_REJECTED",
        resource_type="withdrawal",
        resource_id=tx.id,
        result="success",
        details={"withdrawal_id": tx.id, "reason": reason},
        ip_address=ip,
    )

    await session.commit()
    await session.refresh(tx)

    return {"withdrawal": {"id": tx.id, "status": _tx_state_to_status(tx.state), "state": tx.state}}


@router.post("/{withdrawal_id}/mark-paid")
async def mark_withdrawal_paid(
    withdrawal_id: str,
    request: Request,
    payload: Dict[str, Any] = Body(default={}),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    _require_write(current_admin)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Transaction).where(
        Transaction.id == withdrawal_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "WITHDRAWAL_NOT_FOUND"})

    current_status = _tx_state_to_status(tx.state)
    if current_status not in {"approved", "processing"}:
        raise HTTPException(status_code=409, detail={"error_code": "INVALID_STATE_TRANSITION"})

    reason = (payload.get("reason") or "").strip() or None

    tx.state = "paid"
    tx.status = "paid"
    tx.review_reason = reason
    tx.reviewed_by = str(current_admin.id)
    tx.reviewed_at = datetime.utcnow()

    # paid => held -= amount
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=tx.player_id,
        tx_id=str(tx.id),
        event_type="withdraw_paid",
        delta_available=0.0,
        delta_held=-float(tx.amount),
        currency=tx.currency or "USD",
        idempotency_key=f"withdraw_mark_paid:{tx.id}",
    )

    session.add(tx)

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="WITHDRAWAL_MARK_PAID",
        resource_type="withdrawal",
        resource_id=tx.id,
        result="success",
        details={"withdrawal_id": tx.id, "reason": reason},
        ip_address=ip,
    )

    await session.commit()
    await session.refresh(tx)

    return {"withdrawal": {"id": tx.id, "status": _tx_state_to_status(tx.state), "state": tx.state}}


@router.post("/{withdrawal_id}/mark-failed")
async def mark_withdrawal_failed(
    withdrawal_id: str,
    request: Request,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    _require_write(current_admin)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    reason = (payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail={"error_code": "REASON_REQUIRED"})

    stmt = select(Transaction).where(
        Transaction.id == withdrawal_id,
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail={"error_code": "WITHDRAWAL_NOT_FOUND"})

    if _tx_state_to_status(tx.state) != "processing":
        raise HTTPException(status_code=409, detail={"error_code": "INVALID_STATE_TRANSITION"})

    tx.state = "payout_failed"
    tx.status = "failed"
    tx.review_reason = reason
    tx.reviewed_by = str(current_admin.id)
    tx.reviewed_at = datetime.utcnow()
    session.add(tx)

    request_id = getattr(request.state, "request_id", "unknown")
    ip = request.client.host if request.client else None

    await audit.log_event(
        session=session,
        request_id=request_id,
        actor_user_id=str(current_admin.id),
        tenant_id=tenant_id,
        action="WITHDRAWAL_MARK_FAILED",
        resource_type="withdrawal",
        resource_id=tx.id,
        result="success",
        details={"withdrawal_id": tx.id, "reason": reason},
        ip_address=ip,
    )

    await session.commit()
    await session.refresh(tx)

    return {"withdrawal": {"id": tx.id, "status": _tx_state_to_status(tx.state), "state": tx.state}}


@router.get("/export")
async def export_withdrawals_csv(
    request: Request,
    status: Optional[str] = None,
    q: Optional[str] = None,
    player_id: Optional[str] = None,
    provider_ref: Optional[str] = None,
    sort: str = "created_at_desc",
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # Export is view-level: Support is allowed.
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Transaction, Player).join(Player, Player.id == Transaction.player_id).where(
        Transaction.tenant_id == tenant_id,
        Transaction.type == "withdrawal",
    )
    stmt = _apply_filters(
        stmt,
        tenant_id=tenant_id,
        status=status,
        q=q,
        player_id=player_id,
        provider_ref=provider_ref,
    )
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Player.username.ilike(like)) | (Player.email.ilike(like)))

    if sort == "created_at_asc":
        stmt = stmt.order_by(Transaction.created_at.asc())
    else:
        stmt = stmt.order_by(Transaction.created_at.desc())

    rows = (await session.execute(stmt.limit(5000))).all()

    out_rows: List[Dict[str, Any]] = []
    for tx, player in rows:
        meta = tx.metadata_json or {}
        out_rows.append(
            {
                "withdrawal_id": tx.id,
                "player_id": tx.player_id,
                "player_username": player.username,
                "player_email": player.email,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "status": _tx_state_to_status(tx.state),
                "method": tx.method,
                "destination": meta.get("address") or meta.get("destination") or "",
                "provider": tx.provider or "",
                "provider_ref": tx.provider_tx_id or tx.provider_event_id or "",
                "created_at": tx.created_at.isoformat() if tx.created_at else "",
                "reviewed_by": tx.reviewed_by or "",
                "reviewed_at": tx.reviewed_at.isoformat() if tx.reviewed_at else "",
                "kyc_status": player.kyc_status,
                "risk_score": player.risk_score,
            }
        )

    fieldnames = [
        "withdrawal_id",
        "player_id",
        "player_username",
        "player_email",
        "amount",
        "currency",
        "status",
        "method",
        "destination",
        "provider",
        "provider_ref",
        "created_at",
        "reviewed_by",
        "reviewed_at",
        "kyc_status",
        "risk_score",
    ]

    content = dicts_to_csv_bytes(out_rows, fieldnames=fieldnames)
    filename = f"withdrawals_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
