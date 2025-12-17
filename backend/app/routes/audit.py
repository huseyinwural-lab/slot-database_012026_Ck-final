from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.errors import AppError
from app.models.sql_models import AdminUser, AuditEvent
from app.schemas.audit_event import AuditEventListResponse, AuditEventPublic
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id


router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/events", response_model=AuditEventListResponse)
async def list_audit_events(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    resource_id: Optional[str] = Query(default=None),
    result: Optional[str] = Query(default=None),
    actor_user_id: Optional[str] = Query(default=None),
    request_id: Optional[str] = Query(default=None),
    since_hours: int = Query(default=24, ge=1, le=24 * 30),
    limit: int = Query(default=200, ge=1, le=500),
):
    """List audit events.

    Authorization policy:
    - Owner: can query across tenants (optionally via X-Tenant-ID impersonation).
    - Tenant admin: only sees own tenant (X-Tenant-ID header forbidden by existing policy).
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    q = select(AuditEvent).where(AuditEvent.timestamp >= cutoff)

    # Tenant scoping
    if not getattr(current_admin, "is_platform_owner", False):
        q = q.where(AuditEvent.tenant_id == tenant_id)
    else:
        # Owner can optionally filter to the currently selected tenant scope
        if tenant_id:
            q = q.where(AuditEvent.tenant_id == tenant_id)

    # Filters
    if action:
        q = q.where(AuditEvent.action == action)
    if resource_type:
        q = q.where(AuditEvent.resource_type == resource_type)
    if resource_id:
        q = q.where(AuditEvent.resource_id == resource_id)
    if result:
        q = q.where(AuditEvent.result == result)
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
                tenant_id=e.tenant_id,
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                result=e.result,
                ip_address=e.ip_address,
                details=e.details or {},
            )
            for e in items
        ],
        "meta": {
            "limit": limit,
            "since_hours": since_hours,
        },
    }
