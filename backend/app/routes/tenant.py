from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import Tenant, AdminUser
from app.core.errors import AppError
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

@router.get("/", response_model=dict)
async def list_tenants(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    
    statement = select(Tenant)
    result = await session.execute(statement) # Changed exec to execute for AsyncSession
    tenants = result.scalars().all()
    
    return {
        "items": tenants,
        "meta": {"total": len(tenants), "page": 1}
    }

@router.post("/", response_model=Tenant)
async def create_tenant(
    request: Request,
    tenant_data: Tenant, 
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    
    # Check exists
    stmt = select(Tenant).where(Tenant.name == tenant_data.name)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        raise AppError(error_code="TENANT_EXISTS", message="Tenant exists", status_code=400)
    
    session.add(tenant_data)

    # Audit (owner-only)
    from app.services.audit import audit
    await audit.log(
        admin=current_admin,
        action="tenant.created",
        module="tenants",
        target_id=str(tenant_data.id),
        details={"name": tenant_data.name, "type": tenant_data.type},
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=str(tenant_data.id),
        resource_type="tenant",
        result="success",
    )

    await session.commit()
    await session.refresh(tenant_data)
    
    return tenant_data

@router.get("/capabilities")
async def get_capabilities(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    # Owner impersonation support via header (P0-TENANT-SCOPE): only owner can override.
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    tenant = await session.get(Tenant, tenant_id)
    features = tenant.features if tenant else {}

    return {
        "features": features,
        "is_owner": current_admin.is_platform_owner,
        "tenant_id": tenant_id,
        "tenant_role": current_admin.tenant_role,
        "tenant_name": tenant.name if tenant else "Unknown",
    }


@router.patch("/{tenant_id}")
async def update_tenant_features(
    request: Request,
    tenant_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise AppError(error_code="TENANT_NOT_FOUND", message="Tenant not found", status_code=404)

    # Only update provided keys
    before_features = dict(tenant.features or {})

    if "features" in payload and isinstance(payload["features"], dict):
        tenant.features = payload["features"]

    after_features = dict(tenant.features or {})

    # Diff only (changed keys)
    changed = {}
    keys = set(before_features.keys()) | set(after_features.keys())
    for k in keys:
        if before_features.get(k) != after_features.get(k):
            changed[k] = {"before": before_features.get(k), "after": after_features.get(k)}

    session.add(tenant)

    # Audit (diff-only; masked)
    from app.services.audit import audit
    await audit.log(
        admin=current_admin,
        action="tenant.feature_flags_changed",
        module="tenants",
        target_id=str(tenant.id),
        details={"changed": changed},
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=str(tenant.id),
        resource_type="tenant",
        result="success",
    )

    await session.commit()
    await session.refresh(tenant)

    return {"message": "UPDATED", "tenant": tenant}

# Seeding function adapted for SQL
async def seed_default_tenants(session: AsyncSession):
    # Check if default exists
    stmt = select(Tenant).where(Tenant.id == "default_casino")
    result = await session.execute(stmt)
    if result.scalars().first():
        return

    # Ensure demo_renter is also cleanly re-created if needed

    # Create Owner Tenant
    owner = Tenant(
        id="default_casino", 
        name="Default Casino", 
        type="owner",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_experiments": True,
            "can_use_kill_switch": True,
            "can_manage_affiliates": True,
            "can_use_crm": True,
        }
    )
    
    # Create Demo Renter
    renter = Tenant(
        id="demo_renter",
        name="Demo Renter",
        type="renter",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_affiliates": False,
            "can_use_crm": False,
            "can_manage_experiments": False,
            "can_use_kill_switch": False,
        }
    )
    
    session.add(owner)
    session.add(renter)
    await session.commit()
    print("✅ SQL Tenants Seeded")
