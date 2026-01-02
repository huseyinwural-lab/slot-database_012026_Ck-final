from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
import csv
import io
import uuid
from typing import Optional

from app.core.database import get_session
from app.models.sql_models import AdminUser, AuditEvent
from app.schemas.audit_event import AuditEventListResponse, AuditEventPublic
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.audit import audit # Import service to log export itself

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

@router.get("/events", response_model=AuditEventListResponse)
async def list_audit_events(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    resource_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    actor_user_id: Optional[str] = Query(default=None),
    request_id: Optional[str] = Query(default=None),
    since_hours: int = Query(default=24, ge=1, le=24 * 30),
    limit: int = Query(default=200, ge=1, le=500),
):
    """List audit events."""

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # DB stores TIMESTAMP WITHOUT TIME ZONE, keep comparisons naive UTC.
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)

    q = select(AuditEvent).where(AuditEvent.timestamp >= cutoff)

    # Tenant scoping
    if not getattr(current_admin, "is_platform_owner", False):
        q = q.where(AuditEvent.tenant_id == tenant_id)
    else:
        header_tenant = (request.headers.get("X-Tenant-ID") or "").strip()
        if header_tenant:
            q = q.where(AuditEvent.tenant_id == tenant_id)

    # Filters
    if action:
        q = q.where(AuditEvent.action == action)
    if resource_type:
        q = q.where(AuditEvent.resource_type == resource_type)
    if resource_id:
        q = q.where(AuditEvent.resource_id == resource_id)
    if status:
        q = q.where(AuditEvent.status == status)
    if actor_user_id:
        q = q.where(AuditEvent.actor_user_id == actor_user_id)
    if request_id:
        q = q.where(AuditEvent.request_id == request_id)

    q = q.order_by(AuditEvent.timestamp.desc()).limit(limit)

    res = await session.execute(q)
    items = res.scalars().all()

    return {
        "items": [
            AuditEventPublic(
                id=e.id,
                timestamp=e.timestamp,
                request_id=e.request_id,
                actor_user_id=e.actor_user_id,
                actor_role=e.actor_role,
                tenant_id=e.tenant_id,
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                result=e.result,
                status=e.status,
                reason=e.reason,
                ip_address=e.ip_address,
                user_agent=e.user_agent,
                details=e.details or {},
                before_json=e.before_json,
                after_json=e.after_json,
                diff_json=e.diff_json,
                metadata_json=e.metadata_json,
                error_code=e.error_code,
                error_message=e.error_message
            )
            for e in items
        ],
        "meta": {
            "limit": limit,
            "since_hours": since_hours,
        },
    }

@router.get("/export", response_class=Response)
async def export_audit_events(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
    since_hours: int = Query(default=24, ge=1, le=24 * 90),
):
    """
    Export audit events as CSV.
    Security: Tenant-scoped. Rate-limiting suggested (omitted for MVP, handled by generic rate-limiter).
    Audit: This action itself is audited as 'AUDIT_EXPORT'.
    """
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    # 1. Self-Audit First
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=tenant_id,
        action="AUDIT_EXPORT",
        resource_type="audit_log",
        resource_id=None,
        result="success",
        status="SUCCESS",
        reason="Manual CSV Export",
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        details={"since_hours": since_hours, "format": "csv"}
    )
    # Commit audit log before streaming response to ensure it's recorded even if export fails mid-stream
    await session.commit()
    
    # 2. Query
    # DB stores TIMESTAMP WITHOUT TIME ZONE, keep comparisons naive UTC.
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    q = select(AuditEvent).where(AuditEvent.timestamp >= cutoff)
    
    if not getattr(current_admin, "is_platform_owner", False):
        q = q.where(AuditEvent.tenant_id == tenant_id)
    else:
        header_tenant = (request.headers.get("X-Tenant-ID") or "").strip()
        if header_tenant:
            q = q.where(AuditEvent.tenant_id == tenant_id)
            
    q = q.order_by(AuditEvent.timestamp.desc()).limit(10000)
    
    res = await session.execute(q)
    items = res.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ["timestamp", "action", "status", "reason", "actor", "resource_type", "resource_id", "request_id", "ip"]
    writer.writerow(headers)
    
    for item in items:
        writer.writerow([
            item.timestamp.isoformat(),
            item.action,
            item.status,
            item.reason or "",
            item.actor_user_id,
            item.resource_type,
            item.resource_id or "",
            item.request_id,
            item.ip_address or ""
        ])
        
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=audit_export_{datetime.now().strftime('%Y%m%d')}.csv"})
