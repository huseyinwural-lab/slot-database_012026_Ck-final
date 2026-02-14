from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Request, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.errors import AppError
from app.models.sql_models import Tenant
from app.services.audit import audit
from app.services.system_flags import FLAG_DEFS, get_system_flags, update_system_flag
from app.utils.auth import get_current_admin, AdminUser
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SystemFeatureFlag(BaseModel):
    key: str
    description: str
    enabled: bool


class SystemFeatureFlagUpdate(BaseModel):
    enabled: bool = Field(...)
    reason: str = Field(..., min_length=3)


@router.get("/")
async def get_settings():
    return {"theme": "default", "maintenance": False}


@router.get("/feature-flags", response_model=list[SystemFeatureFlag])
async def list_system_feature_flags(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    if not (current_admin.is_platform_owner or (current_admin.tenant_role or "") == "tenant_admin"):
        raise AppError("UNAUTHORIZED", "Only owner/admin can view feature flags", 403)

    flags = await get_system_flags(session)
    return [
        SystemFeatureFlag(
            key=key,
            description=str(meta.get("description")),
            enabled=bool(meta.get("enabled")),
        )
        for key, meta in flags.items()
    ]


@router.put("/feature-flags/{flag_key}", response_model=SystemFeatureFlag)
async def update_feature_flag(
    flag_key: str,
    payload: SystemFeatureFlagUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    if flag_key not in FLAG_DEFS:
        raise AppError("INVALID_FLAG", "Unknown feature flag", 404)
    if not (current_admin.is_platform_owner or (current_admin.tenant_role or "") == "tenant_admin"):
        raise AppError("UNAUTHORIZED", "Only owner/admin can update feature flags", 403)

    flags = await get_system_flags(session)
    before_state = flags.get(flag_key, {}).get("enabled")

    update_meta = await update_system_flag(session, flag_key, payload.enabled)

    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", "unknown"),
        actor_user_id=str(current_admin.id),
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="system.feature_flag_updated",
        resource_type="system_setting",
        resource_id=flag_key,
        result="success",
        reason=payload.reason,
        before={"enabled": before_state},
        after={"enabled": update_meta.get("after")},
        details={"flag": flag_key},
    )
    await session.commit()

    return SystemFeatureFlag(
        key=flag_key,
        description=str(FLAG_DEFS[flag_key]["description"]),
        enabled=bool(update_meta.get("after")),
    )


@router.get("/brands")
async def get_brands(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # UI expects ARRAY of brands, not {items: [...]}
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # MVP: represent "brands" using Tenant table.
    # Owner can impersonate via X-Tenant-ID header; tenant admins only see their own tenant.
    stmt = select(Tenant)
    if not current_admin.is_platform_owner:
        stmt = stmt.where(Tenant.id == tenant_id)

    tenants = (await session.execute(stmt)).scalars().all()

    now = datetime.utcnow().isoformat()
    return [
        {
            "id": t.id,
            "brand_name": t.name,
            "status": "active",
            "default_currency": "USD",
            "default_language": "en",
            "country_availability": [],
            "created_at": (t.created_at.isoformat() if getattr(t, "created_at", None) else now),
        }
        for t in tenants
    ]


@router.post("/brands")
async def create_brand(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # Minimal: create a new Tenant as a brand.
    # Guard: only platform owner should create brands/tenants.
    if not current_admin.is_platform_owner:
        raise AppError("UNAUTHORIZED", "Only platform owner can create brands", 403)

    name = (payload.get("brand_name") or payload.get("name") or "").strip()
    if not name:
        raise AppError("VALIDATION_ERROR", "brand_name is required", 422)

    # ensure unique
    existing = (await session.execute(select(Tenant).where(Tenant.name == name))).scalars().first()
    if existing:
        raise AppError("TENANT_EXISTS", "Brand already exists", 400)

    tenant = Tenant(name=name, type="renter", features={})
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)

    return {"id": tenant.id}

