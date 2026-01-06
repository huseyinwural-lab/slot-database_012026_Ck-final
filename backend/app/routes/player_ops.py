from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.player_ops_models import PlayerManualBonusGrant, PlayerSessionRevocation
from app.models.sql_models import AdminUser, Player
from app.services.audit import audit
from app.services.wallet_ledger import WalletInvariantError, apply_wallet_delta_with_ledger
from app.utils.auth import get_current_admin, get_current_admin_from_token
from app.utils.reason import require_reason
from app.utils.tenant import get_current_tenant_id


router = APIRouter(prefix="/api/v1/players", tags=["player_ops"])


def _require_any_role(current_admin: AdminUser, allowed: set[str]) -> None:
    role = (getattr(current_admin, "role", None) or "").strip()
    # treat Super Admin as all-allowed
    if role == "Super Admin":
        return

    if role not in allowed:
        raise HTTPException(status_code=403, detail={"error_code": "FORBIDDEN"})


async def _get_player_or_404(session: AsyncSession, *, tenant_id: str, player_id: str) -> Player:
    stmt = select(Player).where(Player.id == player_id, Player.tenant_id == tenant_id)
    player = (await session.execute(stmt)).scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


async def _audit_event(
    *,
    session: AsyncSession,
    request: Request,
    admin: AdminUser,
    tenant_id: str,
    action: str,
    player_id: str,
    reason: str,
    payload: Dict[str, Any],
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    status: str = "SUCCESS",
    result: str = "success",
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    try:
        await audit.log_event(
            session=session,
            request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
            actor_user_id=str(admin.id),
            actor_role=getattr(admin, "role", None),
            tenant_id=str(tenant_id),
            action=action,
            resource_type="player",
            resource_id=str(player_id),
            result=result,
            status=status,
            reason=reason,
            ip_address=getattr(request.state, "ip_address", None),
            user_agent=getattr(request.state, "user_agent", None),
            details={"payload": payload},
            before=before,
            after=after,
            error_code=error_code,
            error_message=error_message,
        )
    except Exception:
        # best effort
        try:
            await session.rollback()
        except Exception:
            pass


@router.post("/{player_id}/credit")
async def manual_credit(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    # RBAC: Admin+
    _require_any_role(current_admin, {"Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    amount = float(payload.get("amount") or 0)
    currency = (payload.get("currency") or "USD").strip() or "USD"
    if amount <= 0:
        raise HTTPException(status_code=400, detail={"error_code": "AMOUNT_INVALID"})

    before = {
        "balance_real_available": float(player.balance_real_available or 0.0),
        "balance_real_held": float(player.balance_real_held or 0.0),
        "balance_real": float(player.balance_real or 0.0),
    }

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_CREDIT_ATTEMPT",
        player_id=player.id,
        reason=reason,
        payload={"amount": amount, "currency": currency},
        before=before,
        status="SUCCESS",
        result="success",
    )

    tx_id = str(uuid.uuid4())
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=player.id,
        tx_id=tx_id,
        event_type="manual_credit",
        delta_available=float(amount),
        delta_held=0.0,
        currency=currency,
        idempotency_key=None,
        provider="admin",
        provider_ref=reason,
        provider_event_id=f"player_credit:{tx_id}",
        allow_negative=False,
    )

    # Keep legacy aggregate balances in sync
    player.balance_real_available = float(player.balance_real_available or 0.0)
    player.balance_real_held = float(player.balance_real_held or 0.0)
    player.balance_real = float(player.balance_real_available) + float(player.balance_real_held)
    session.add(player)

    await session.commit()
    await session.refresh(player)

    after = {
        "balance_real_available": float(player.balance_real_available or 0.0),
        "balance_real_held": float(player.balance_real_held or 0.0),
        "balance_real": float(player.balance_real or 0.0),
    }

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_CREDIT",
        player_id=player.id,
        reason=reason,
        payload={"amount": amount, "currency": currency, "tx_id": tx_id},
        before=before,
        after=after,
        status="SUCCESS",
        result="success",
    )

    return {"status": "ok", "tx_id": tx_id, "wallet": after}


@router.post("/{player_id}/debit")
async def manual_debit(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    # RBAC: Admin+
    _require_any_role(current_admin, {"Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    amount = float(payload.get("amount") or 0)
    currency = (payload.get("currency") or "USD").strip() or "USD"
    if amount <= 0:
        raise HTTPException(status_code=400, detail={"error_code": "AMOUNT_INVALID"})

    available = float(player.balance_real_available or 0.0)
    if available < amount:
        raise HTTPException(status_code=409, detail={"error_code": "INSUFFICIENT_FUNDS"})

    before = {
        "balance_real_available": float(player.balance_real_available or 0.0),
        "balance_real_held": float(player.balance_real_held or 0.0),
        "balance_real": float(player.balance_real or 0.0),
    }

    tx_id = str(uuid.uuid4())
    await apply_wallet_delta_with_ledger(
        session,
        tenant_id=tenant_id,
        player_id=player.id,
        tx_id=tx_id,
        event_type="manual_debit",
        delta_available=-float(amount),
        delta_held=0.0,
        currency=currency,
        idempotency_key=None,
        provider="admin",
        provider_ref=reason,
        provider_event_id=f"player_debit:{tx_id}",
        allow_negative=False,
    )

    player.balance_real_available = float(player.balance_real_available or 0.0)
    player.balance_real_held = float(player.balance_real_held or 0.0)
    player.balance_real = float(player.balance_real_available) + float(player.balance_real_held)
    session.add(player)

    await session.commit()
    await session.refresh(player)

    after = {
        "balance_real_available": float(player.balance_real_available or 0.0),
        "balance_real_held": float(player.balance_real_held or 0.0),
        "balance_real": float(player.balance_real or 0.0),
    }

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_DEBIT",
        player_id=player.id,
        reason=reason,
        payload={"amount": amount, "currency": currency, "tx_id": tx_id},
        before=before,
        after=after,
        status="SUCCESS",
        result="success",
    )

    return {"status": "ok", "tx_id": tx_id, "wallet": after}


@router.get("/{player_id}/bonuses")
async def list_manual_bonuses(
    player_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    _require_any_role(current_admin, {"Support", "Ops", "Admin"})
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # tenant boundary
    await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    stmt = (
        select(PlayerManualBonusGrant)
        .where(PlayerManualBonusGrant.tenant_id == tenant_id, PlayerManualBonusGrant.player_id == player_id)
        .order_by(PlayerManualBonusGrant.created_at.desc())
        .limit(200)
    )
    rows = (await session.execute(stmt)).scalars().all()

    return [
        {
            "id": r.id,
            "bonus_type": r.bonus_type,
            "amount": r.amount,
            "quantity": r.quantity,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "reason": r.reason,
            "created_by_admin_id": r.created_by_admin_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/{player_id}/bonuses")
async def grant_manual_bonus(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    # RBAC: Admin+
    _require_any_role(current_admin, {"Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    bonus_type = (payload.get("bonus_type") or "").strip()
    amount = payload.get("amount")
    quantity = payload.get("quantity")
    expires_at = payload.get("expires_at")

    if bonus_type not in {"cash", "free_spins"}:
        raise HTTPException(status_code=400, detail={"error_code": "BONUS_TYPE_INVALID"})

    if bonus_type == "cash":
        if amount is None or float(amount) <= 0:
            raise HTTPException(status_code=400, detail={"error_code": "AMOUNT_REQUIRED"})
        qty_val = None
        amt_val = float(amount)
    else:
        if quantity is None or int(quantity) <= 0:
            raise HTTPException(status_code=400, detail={"error_code": "QUANTITY_REQUIRED"})
        amt_val = None
        qty_val = int(quantity)

    exp_dt: Optional[datetime] = None
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at)
        except Exception:
            raise HTTPException(status_code=400, detail={"error_code": "EXPIRY_INVALID"})

    # For cash bonus, also credit bonus balance (simple MVP)
    before_bal = {
        "balance_bonus": float(player.balance_bonus or 0.0),
        "wagering_requirement": float(player.wagering_requirement or 0.0),
        "wagering_remaining": float(player.wagering_remaining or 0.0),
    }

    grant = PlayerManualBonusGrant(
        tenant_id=tenant_id,
        player_id=player.id,
        bonus_type=bonus_type,
        amount=amt_val,
        quantity=qty_val,
        expires_at=exp_dt,
        reason=reason,
        created_by_admin_id=str(current_admin.id),
    )
    session.add(grant)

    if bonus_type == "cash":
        player.balance_bonus = float(player.balance_bonus or 0.0) + float(amt_val)
        session.add(player)

    await session.commit()
    await session.refresh(grant)

    after_bal = {
        "balance_bonus": float(player.balance_bonus or 0.0),
        "wagering_requirement": float(player.wagering_requirement or 0.0),
        "wagering_remaining": float(player.wagering_remaining or 0.0),
    }

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_BONUS_GRANT",
        player_id=player.id,
        reason=reason,
        payload={
            "bonus_type": bonus_type,
            "amount": amt_val,
            "quantity": qty_val,
            "expires_at": expires_at,
            "grant_id": grant.id,
        },
        before=before_bal,
        after=after_bal,
        status="SUCCESS",
        result="success",
    )

    return {"id": grant.id}


@router.post("/{player_id}/suspend")
async def suspend_player(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    # RBAC: Ops+
    _require_any_role(current_admin, {"Ops", "Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    before = {"status": player.status}
    if player.status == "suspended":
        return {"status": "suspended"}

    player.status = "suspended"
    session.add(player)
    await session.commit()

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_SUSPEND",
        player_id=player.id,
        reason=reason,
        payload={"status": "suspended"},
        before=before,
        after={"status": "suspended"},
        status="SUCCESS",
        result="success",
    )

    return {"status": "suspended"}


@router.post("/{player_id}/unsuspend")
async def unsuspend_player(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    _require_any_role(current_admin, {"Ops", "Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    # state guard
    if player.status != "suspended":
        raise HTTPException(status_code=409, detail={"error_code": "STATE_MISMATCH"})

    before = {"status": player.status}

    player.status = "active"
    session.add(player)
    await session.commit()

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_UNSUSPEND",
        player_id=player.id,
        reason=reason,
        payload={"status": "active"},
        before=before,
        after={"status": "active"},
        status="SUCCESS",
        result="success",
    )

    return {"status": "active"}


@router.post("/{player_id}/force-logout")
async def force_logout(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    _require_any_role(current_admin, {"Ops", "Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    rev = PlayerSessionRevocation(
        tenant_id=tenant_id,
        player_id=player.id,
        revoked_at=datetime.now(timezone.utc),
        revoked_by_admin_id=str(current_admin.id),
        reason=reason,
    )
    session.add(rev)
    await session.commit()
    await session.refresh(rev)

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_FORCE_LOGOUT",
        player_id=player.id,
        reason=reason,
        payload={"revoked_at": rev.revoked_at.isoformat()},
        status="SUCCESS",
        result="success",
    )

    return {"status": "ok"}


@router.post("/{player_id}/notes")
async def add_internal_note(
    player_id: str,
    request: Request,
    payload: dict = Body(default={}),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin_from_token),
):
    _require_any_role(current_admin, {"Support", "Ops", "Admin"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await _get_player_or_404(session, tenant_id=tenant_id, player_id=player_id)

    note = (payload.get("note") or "").strip()
    if not note:
        raise HTTPException(status_code=400, detail={"error_code": "NOTE_REQUIRED"})

    await _audit_event(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="PLAYER_NOTE",
        player_id=player.id,
        reason=reason,
        payload={"note": note},
        status="SUCCESS",
        result="success",
    )
    await session.commit()

    return {"status": "ok"}
