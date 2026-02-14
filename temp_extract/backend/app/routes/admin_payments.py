from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta, timezone

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.models.payment_models import PaymentIntent
from app.models.payment_analytics_models import PaymentAttempt
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/admin/payments", tags=["payment_analytics"])

@router.get("/metrics")
async def get_payment_metrics(
    tenant_id: str = None,
    provider: str = None,
    since_hours: int = 24,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Tenant Scope
    effective_tenant = await get_current_tenant_id(None, current_admin, session=session)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    
    # Base Query
    stmt = select(PaymentAttempt).where(PaymentAttempt.created_at >= cutoff)
    stmt = stmt.where(PaymentAttempt.tenant_id == effective_tenant)
    
    if provider:
        stmt = stmt.where(PaymentAttempt.provider == provider)
        
    attempts = (await session.execute(stmt)).scalars().all()
    
    if not attempts:
        return {"success_rate": 0, "total": 0}
        
    total = len(attempts)
    success = sum(1 for a in attempts if a.status == "SUCCESS")
    failed = sum(1 for a in attempts if a.status == "FAILED" or a.status == "DECLINED")
    soft_decline = sum(1 for a in attempts if a.retryable)
    
    latency_sum = sum(a.latency_ms for a in attempts)
    
    # Decline Codes
    codes = {}
    for a in attempts:
        if a.raw_code:
            codes[a.raw_code] = codes.get(a.raw_code, 0) + 1
            
    return {
        "total_attempts": total,
        "success_count": success,
        "success_rate": round(success / total, 4),
        "fail_rate": round(failed / total, 4),
        "soft_decline_rate": round(soft_decline / total, 4),
        "avg_latency_ms": round(latency_sum / total, 2),
        "top_decline_codes": dict(sorted(codes.items(), key=lambda item: item[1], reverse=True)[:5])
    }

@router.get("/intents/{intent_id}")
async def get_intent_timeline(
    intent_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    effective_tenant = await get_current_tenant_id(None, current_admin, session=session)
    
    intent = await session.get(PaymentIntent, intent_id)
    if not intent or intent.tenant_id != effective_tenant:
        raise HTTPException(404, "Intent not found")
        
    stmt = select(PaymentAttempt).where(PaymentAttempt.payment_intent_id == intent_id).order_by(PaymentAttempt.attempt_no)
    attempts = (await session.execute(stmt)).scalars().all()
    
    return {
        "intent": intent,
        "timeline": attempts
    }
