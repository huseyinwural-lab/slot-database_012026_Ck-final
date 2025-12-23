from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import List
from datetime import datetime, timezone, timedelta
import uuid

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser, PayoutAttempt, Tenant, AuditEvent
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.audit import audit
from app.services.psp import get_psp

router = APIRouter(prefix="/api/v1/finance-actions", tags=["finance_actions"])

@router.post("/withdrawals/{tx_id}/retry")
async def retry_payout(
    tx_id: str,
    request: Request,
    payload: dict = Body(default={}),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Retry a failed or stuck withdrawal payout.
    Enforces TENANT-POLICY-002:
    - Payout Retry Limit
    - Payout Cooldown
    """
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required for retrying payout")

    effective_tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # 1. Fetch Transaction & Tenant Policy
    stmt = select(Transaction).where(
        Transaction.id == tx_id,
        Transaction.tenant_id == effective_tenant_id
    )
    tx = (await session.execute(stmt)).scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx.type != "withdrawal":
        raise HTTPException(status_code=400, detail="Transaction is not a withdrawal")

    tenant = await session.get(Tenant, effective_tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # 2. Check Attempts
    attempts_stmt = select(PayoutAttempt).where(PayoutAttempt.withdraw_tx_id == tx_id).order_by(PayoutAttempt.created_at.desc())
    attempts = (await session.execute(attempts_stmt)).scalars().all()
    count = len(attempts)
    last_attempt = attempts[0] if attempts else None

    # Policy 1: Retry Limit
    limit = tenant.payout_retry_limit or 3 # Default 3
    if count >= limit:
        await audit.log_event(
            session=session,
            request_id=request.headers.get("X-Request-Id", "unknown"),
            actor_user_id=current_admin.id,
            tenant_id=effective_tenant_id,
            action="FIN_PAYOUT_RETRY_BLOCKED",
            resource_type="withdrawal",
            resource_id=tx_id,
            result="blocked",
            details={"reason": "limit_exceeded", "limit": limit, "count": count},
            ip_address=request.client.host
        )
        await session.commit()
        raise HTTPException(status_code=422, detail={"error_code": "PAYMENT_RETRY_LIMIT_EXCEEDED", "message": f"Retry limit ({limit}) exceeded."})

    # Policy 2: Cooldown
    cooldown = tenant.payout_cooldown_seconds or 60 # Default 60s
    if last_attempt:
        elapsed = (datetime.utcnow() - last_attempt.created_at).total_seconds()
        if elapsed < cooldown:
            await audit.log_event(
                session=session,
                request_id=request.headers.get("X-Request-Id", "unknown"),
                actor_user_id=current_admin.id,
                tenant_id=effective_tenant_id,
                action="FIN_PAYOUT_RETRY_BLOCKED",
                resource_type="withdrawal",
                resource_id=tx_id,
                result="blocked",
                details={"reason": "cooldown_active", "cooldown": cooldown, "elapsed": elapsed},
                ip_address=request.client.host
            )
            await session.commit()
            raise HTTPException(status_code=429, detail={"error_code": "PAYMENT_COOLDOWN_ACTIVE", "message": f"Please wait {int(cooldown - elapsed)}s before retrying."})

    # 3. Create New Attempt
    attempt = PayoutAttempt(
        withdraw_tx_id=tx.id,
        tenant_id=effective_tenant_id,
        provider=tx.provider or "mock_psp", # Default or existing
        status="pending",
        idempotency_key=str(uuid.uuid4())
    )
    session.add(attempt)
    
    # 4. Trigger Logic (Stubbed for now, just recording attempt)
    # In real flow, this would call PSP service.
    
    await audit.log_event(
        session=session,
        request_id=request.headers.get("X-Request-Id", "unknown"),
        actor_user_id=current_admin.id,
        tenant_id=effective_tenant_id,
        action="FIN_PAYOUT_RETRY_INITIATED",
        resource_type="withdrawal",
        resource_id=tx_id,
        result="success",
        details={"attempt_id": attempt.id, "reason": reason},
        ip_address=request.client.host
    )
    
    await session.commit()
    return {"status": "retry_initiated", "attempt_id": attempt.id}
