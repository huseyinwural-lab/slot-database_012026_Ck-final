from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import Tenant, AdminUser
from app.core.errors import AppError
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner
from app.schemas.tenant import TenantCreateRequest
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
    payload: TenantCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    from app.services.audit import audit

    # Audit attempt (success/failed/denied must be visible)
    await audit.log(
        admin=current_admin,
        action="tenant.create.attempt",
        module="tenants",
        target_id=None,
        details={"name": payload.name, "type": payload.type},
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=getattr(current_admin, "tenant_id", None),
        resource_type="tenant",
        result="success",  # attempt itself is successful; outcome is recorded below
    )

    # Hard stop: only platform owner can create tenants
    try:
        require_owner(current_admin)
    except Exception:
        await audit.log(
            admin=current_admin,
            action="tenant.create.attempt",
            module="tenants",
            target_id=None,
            details={"name": payload.name, "type": payload.type, "denied": True},
            session=session,
            request_id=getattr(request.state, "request_id", None),
            tenant_id=getattr(current_admin, "tenant_id", None),
            resource_type="tenant",
            result="blocked",
        )
        raise

    # Create (server-side ignore/forbid unknown fields such as is_system)
    tenant_data = Tenant(
        name=payload.name,
        type=payload.type,
        features=payload.features or {},
    )

    # Check exists
    stmt = select(Tenant).where(Tenant.name == tenant_data.name)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        await audit.log(
            admin=current_admin,
            action="tenant.create.attempt",
            module="tenants",
            target_id=None,
            details={"name": payload.name, "type": payload.type, "error": "TENANT_EXISTS"},
            session=session,
            request_id=getattr(request.state, "request_id", None),
            tenant_id=getattr(current_admin, "tenant_id", None),
            resource_type="tenant",
            result="failed",
        )
        raise AppError(error_code="TENANT_EXISTS", message="Tenant exists", status_code=400)

    session.add(tenant_data)

    # Audit: created
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


def require_tenant_policy_admin(admin: AdminUser) -> None:
    """Allow platform owner or tenant_admin to edit payment policy."""
    if not (admin.is_platform_owner or (admin.tenant_role or "") == "tenant_admin"):
        raise HTTPException(status_code=403, detail={"error_code": "UNAUTHORIZED"})


@router.get("/payments/policy")
async def get_payments_policy(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise AppError(error_code="TENANT_NOT_FOUND", message="Tenant not found", status_code=404)

    return {
        "tenant_id": tenant.id,
        "daily_deposit_limit": tenant.daily_deposit_limit,
        "daily_withdraw_limit": tenant.daily_withdraw_limit,
        "payout_retry_limit": tenant.payout_retry_limit,
        "payout_cooldown_seconds": tenant.payout_cooldown_seconds,
    }


@router.put("/payments/policy")
async def update_payments_policy(
    request: Request,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    require_tenant_policy_admin(current_admin)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise AppError(error_code="TENANT_NOT_FOUND", message="Tenant not found", status_code=404)

    before = {
        "daily_deposit_limit": tenant.daily_deposit_limit,
        "daily_withdraw_limit": tenant.daily_withdraw_limit,
        "payout_retry_limit": tenant.payout_retry_limit,
        "payout_cooldown_seconds": tenant.payout_cooldown_seconds,
    }

    for field in before.keys():
        if field in payload:
            setattr(tenant, field, payload[field])

    after = {k: getattr(tenant, k) for k in before.keys()}

    session.add(tenant)

    # Audit event for policy update
    from app.services.audit import audit

    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", "unknown"),
        actor_user_id=str(current_admin.id),
        tenant_id=tenant.id,
        action="TENANT_POLICY_UPDATED",
        resource_type="tenant_policy",
        resource_id=tenant.id,
        result="success",
        details={"before": before, "after": after},
        ip_address=request.client.host if request.client else None,
    )

    await session.commit()
    await session.refresh(tenant)

    return {"message": "UPDATED", "policy": after}



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

@router.get("/{tenant_id}/menu-flags")
async def get_menu_flags(
    tenant_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise AppError(error_code="TENANT_NOT_FOUND", message="Tenant not found", status_code=404)
        
    features = tenant.features or {}
    return features.get("menu_flags", {})

@router.patch("/{tenant_id}/menu-flags")
async def update_menu_flags(
    tenant_id: str,
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    require_owner(current_admin)
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise AppError(error_code="TENANT_NOT_FOUND", message="Tenant not found", status_code=404)
        
    # Deep merge logic for menu_flags
    current_features = dict(tenant.features or {})
    current_flags = current_features.get("menu_flags", {})
    
    # Payload is expected to be { key: bool, ... }
    # Merge new flags into existing flags
    updated_flags = {**current_flags, **payload}
    
    # Update features
    current_features["menu_flags"] = updated_flags
    tenant.features = current_features # SQLModel detects change on assignment
    
    session.add(tenant)
    
    # Audit
    from app.services.audit import audit
    await audit.log(
        admin=current_admin,
        action="tenant.menu_flags_updated",
        module="tenants",
        target_id=str(tenant.id),
        details={"updated_flags": payload},
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=str(tenant.id),
        resource_type="tenant",
        result="success",
    )
    
    await session.commit()
    return {"message": "Menu flags updated", "menu_flags": updated_flags}

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
            "can_use_game_robot": True,
            "can_manage_kyc": True,
            "can_manage_bonus": True,
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
            "can_use_game_robot": True,
            "can_manage_kyc": True,
            "can_manage_bonus": True,
        }
    )
    
    session.add(owner)
    session.add(renter)
    await session.commit()
    print("✅ SQL Tenants Seeded")
