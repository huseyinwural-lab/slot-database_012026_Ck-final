from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
import uuid

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser, PayoutAttempt, Tenant
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.audit import audit

from app.services.metrics import metrics
from config import settings
router = APIRouter(prefix="/api/v1/finance-actions", tags=["finance_actions"])
import logging
logger = logging.getLogger(__name__)

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
    cooldown = tenant.payout_cooldown_seconds or 60  # Default 60s
    if last_attempt:
        # IMPORTANT (CI stability): Some DB columns are TIMESTAMP WITHOUT TIME ZONE.
        # Normalize all comparisons to *naive UTC* to avoid
        # "can't subtract offset-naive and offset-aware datetimes".
        now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        last_created = last_attempt.created_at
        if getattr(last_created, "tzinfo", None) is not None:
            last_created = last_created.astimezone(timezone.utc).replace(tzinfo=None)

        elapsed = (now_naive_utc - last_created).total_seconds()
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
                ip_address=request.client.host,
            )
            await session.commit()
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": "PAYMENT_COOLDOWN_ACTIVE",
                    "message": f"Please wait {int(cooldown - elapsed)}s before retrying.",
                },
            )

    # 3. Create New Attempt
    attempt = PayoutAttempt(
        withdraw_tx_id=tx.id,
        tenant_id=effective_tenant_id,
        provider=tx.provider or "mock_psp", # Default or existing
        status="pending",
        idempotency_key=str(uuid.uuid4())
    )
    session.add(attempt)
    
    # 4. Trigger Logic
    provider = attempt.provider
    
    # Gating for Mock Provider in Prod (PAYOUT-PROVIDER-001)
    if provider == "mock_psp" or "mock" in provider:
        if settings.env in {"prod", "production"} and not settings.allow_test_payment_methods:
             raise HTTPException(status_code=403, detail="Mock payouts are disabled in production")

    # In real flow, this would call PSP service.
    # We simulate async processing
    if provider == "mock_psp":
        # Simulate success
        tx.status = "completed" # For simplicity in this sprint
        attempt.status = "success"
        session.add(tx)
    # REAL PAYOUT PROVIDER INTEGRATION (PAYOUT-REAL-001)
    if provider == "adyen":
        # 1. Init Service
        from app.services.adyen_psp import AdyenPSP
        adyen_service = AdyenPSP(
            api_key=settings.adyen_api_key or "mock_key",
            merchant_account=settings.adyen_merchant_account or "mock_merchant"
        )
        
        # 2. Prepare Data
        # We need shopperEmail and shopperReference.
        # Fetch Player
        from app.models.sql_models import Player
        player = await session.get(Player, tx.player_id)
        if not player:
             raise HTTPException(status_code=500, detail="Player not found for payout")
             
        # 3. Call Payout
        try:
            payout_ref = f"payout_{attempt.id}"
            
            metrics.record_payout_attempt()
            
            payout_resp = await adyen_service.submit_payout(
                amount=tx.amount,
                currency=tx.currency,
                reference=payout_ref,
                shopper_reference=player.id,
                shopper_email=player.email,
                bank_account=tx.metadata_json.get("bank_account") if tx.metadata_json else None
            )
            
            # 4. Update Status
            result_code = payout_resp.get("resultCode")
            attempt.provider_event_id = payout_resp.get("pspReference")
            
            if result_code in ["[payout-submit-received]", "Received"]:
                attempt.status = "submitted"
                tx.status = "payout_pending" 
                tx.state = "payout_submitted"
            else:
                 attempt.status = "unknown_response"
                 
        except Exception as e:
            logger.error(f"Adyen Payout Failed: {e}")
            attempt.status = "failed"
            attempt.error_code = str(e)
            raise HTTPException(status_code=502, detail=f"Provider Error: {str(e)}")
            
        session.add(attempt)
        session.add(tx)
        await session.commit()
        
        return {"status": "retry_initiated", "attempt_id": attempt.id, "provider_ref": attempt.provider_event_id}

        session.add(attempt)
    
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
