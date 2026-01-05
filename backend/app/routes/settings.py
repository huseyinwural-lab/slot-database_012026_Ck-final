from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.errors import AppError
from app.models.sql_models import Tenant
from app.utils.auth import get_current_admin, AdminUser
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/")
async def get_settings():
    return {"theme": "default", "maintenance": False}


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

