from typing import List
from fastapi import APIRouter, Depends, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin, get_password_hash, create_access_token
from app.core.errors import AppError
from app.utils.permissions import require_owner
from datetime import timedelta
from app.services.audit import audit
from app.schemas.admin import AdminUserPublic
from app.schemas.admin_update import AdminUpdateRequest, AdminStatusRequest
from app.utils.security import sha256_surrogate

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

from app.utils.tenant import get_current_tenant_id


@router.get("/users", response_model=List[AdminUserPublic])
async def get_admins(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    query = select(AdminUser).where(AdminUser.tenant_id == tenant_id)

    result = await session.execute(query)  # Changed exec to execute
    admins = result.scalars().all()
    return [AdminUserPublic.model_validate(a) for a in admins]

@router.post("/users")
async def create_admin(
    request: Request,
    payload: dict = Body(...), 
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    password_mode = payload.get("password_mode") or "set"

    if not email:
        raise AppError("EMAIL_REQUIRED", "Email is required", 400)

    is_invite = password_mode == "invite"
    if (not is_invite) and (not password):
        raise AppError("PASSWORD_REQUIRED", "Password is required", 400)

    existing = (await session.execute(select(AdminUser).where(AdminUser.email == email))).scalars().first()
    if existing:
        raise AppError("USER_EXISTS", "User already exists", 400)

    # Tenant isolation: non-owner cannot override tenant_id
    requested_tenant_id = payload.get("tenant_id")
    if getattr(current_admin, "is_platform_owner", False):
        tenant_id = requested_tenant_id or current_admin.tenant_id
    else:
        if requested_tenant_id and requested_tenant_id != current_admin.tenant_id:
            raise AppError("TENANT_OVERRIDE_FORBIDDEN", "Cannot create admin for another tenant", 403)
        tenant_id = current_admin.tenant_id

    # password_hash must not be empty
    if is_invite and not password:
        import secrets
        password = secrets.token_urlsafe(32)

    new_admin = AdminUser(
        email=email,
        username=email.split("@")[0],
        full_name=payload.get("full_name", "Admin"),
        role=payload.get("role", "Admin"),
        tenant_role=payload.get("tenant_role", "tenant_admin"),
        tenant_id=tenant_id,
        password_hash=get_password_hash(password),
        status="active"
    )

    if is_invite:
        new_admin.status = "invited"
        token = create_access_token({"sub": "invite", "email": email}, timedelta(days=7))
        new_admin.invite_token = token
    
    session.add(new_admin)
    
    await audit.log(
        admin=current_admin,
        action="admin.user_created",
        module="admin",
        target_id=str(new_admin.id),
        details={"email": email, "role": new_admin.role, "target_tenant": new_admin.tenant_id},
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=tenant_id,
        resource_type="admin_user",
        result="success",
    )

    await session.commit()
    await session.refresh(new_admin)


@router.patch("/users/{admin_id}")
async def update_admin_user(
    request: Request,
    admin_id: str,
    payload: AdminUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Update admin user fields (owner only in MVP).

    Audit:
    - admin.user_updated (diff-only)
    - admin.user_role_changed (when role changes)

    PII policy: raw email/username are NOT stored in audit; only sha256 surrogates.
    """

    require_owner(current_admin)

    admin = await session.get(AdminUser, admin_id)
    if not admin:
        raise AppError("ADMIN_NOT_FOUND", "Admin not found", 404)

    tenant_id = admin.tenant_id

    changes = {}

    def record_change(key: str, before, after, pii: bool = False):
        if before == after:
            return
        if pii:
            changes[key] = {
                "changed": True,
                "before_hash": sha256_surrogate(before or ""),
                "after_hash": sha256_surrogate(after or ""),
            }
        else:
            changes[key] = {"before": before, "after": after}

    # full_name (safe)
    if payload.full_name is not None:
        record_change("full_name", admin.full_name, payload.full_name, pii=False)
        admin.full_name = payload.full_name

    # email (PII)
    if payload.email is not None:
        new_email = str(payload.email).strip().lower()
        record_change("email", admin.email, new_email, pii=True)
        admin.email = new_email
        # keep username in sync (PII-ish) but do not log raw
        admin.username = new_email.split("@")[0]

    # role (safe-ish but triggers dedicated event)
    role_changed = False
    if payload.role is not None:
        record_change("role", admin.role, payload.role, pii=False)
        role_changed = admin.role != payload.role
        admin.role = payload.role

    # tenant_role
    if payload.tenant_role is not None:
        record_change("tenant_role", admin.tenant_role, payload.tenant_role, pii=False)
        admin.tenant_role = payload.tenant_role

    session.add(admin)

    request_id = getattr(request.state, "request_id", "unknown")
    client_ip = request.client.host if request.client else "unknown"

    if changes:
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=str(tenant_id),
            action="admin.user_updated",
            resource_type="admin_user",
            resource_id=str(admin.id),
            result="success",
            details={"changed": changes},
            ip_address=client_ip,
        )

        if role_changed:
            await audit.log_event(
                session=session,
                request_id=request_id,
                actor_user_id=str(current_admin.id),
                tenant_id=str(tenant_id),
                action="admin.user_role_changed",
                resource_type="admin_user",
                resource_id=str(admin.id),
                result="success",
                details={"changed": {"role": changes.get("role")}},
                ip_address=client_ip,
            )

    await session.commit()
    await session.refresh(admin)

    return {"user": AdminUserPublic.model_validate(admin)}


@router.post("/users/{admin_id}/status")
async def set_admin_status(
    request: Request,
    admin_id: str,
    payload: AdminStatusRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Enable/disable an admin user (owner only in MVP)."""

    require_owner(current_admin)

    admin = await session.get(AdminUser, admin_id)
    if not admin:
        raise AppError("ADMIN_NOT_FOUND", "Admin not found", 404)

    before = admin.is_active
    admin.is_active = payload.is_active
    admin.status = "active" if payload.is_active else "disabled"

    session.add(admin)

    request_id = getattr(request.state, "request_id", "unknown")
    client_ip = request.client.host if request.client else "unknown"

    if before != payload.is_active:
        await audit.log_event(
            session=session,
            request_id=request_id,
            actor_user_id=str(current_admin.id),
            tenant_id=str(admin.tenant_id),
            action="admin.user_enabled" if payload.is_active else "admin.user_disabled",
            resource_type="admin_user",
            resource_id=str(admin.id),
            result="success",
            details={"changed": {"is_active": {"before": before, "after": payload.is_active}}},
            ip_address=client_ip,
        )

    await session.commit()
    await session.refresh(admin)

    return {"user": AdminUserPublic.model_validate(admin)}


@router.post("/create-tenant-admin")
async def create_tenant_admin(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Owner-only: create a tenant admin for a given tenant.

    Payload (minimum):
    - email
    - tenant_id
    - password (required)
    
    Optional:
    - full_name

    This is primarily for ops/testing (SEC-001).
    """

    require_owner(current_admin)

    email = (payload.get("email") or "").strip().lower()
    tenant_id = (payload.get("tenant_id") or "").strip() or "demo_renter"
    password = payload.get("password")
    if not password:
        raise AppError(error_code="PASSWORD_REQUIRED", message="Password is required", status_code=400)
    full_name = payload.get("full_name") or "Tenant Admin"

    stmt = select(AdminUser).where(AdminUser.email == email)
    res = await session.execute(stmt)
    if res.scalars().first():
        raise AppError(error_code="ADMIN_EXISTS", message="Admin already exists", status_code=400)

    new_admin = AdminUser(
        email=email,
        username=email.split("@")[0],
        full_name=full_name,
        role="Tenant Admin",
        tenant_role="tenant_admin",
        tenant_id=tenant_id,
        password_hash=get_password_hash(password),
        is_platform_owner=False,
        status="active",
        is_active=True,
    )

    session.add(new_admin)
    await audit.log(
        admin=current_admin,
        action="tenant.admin_created",
        module="admin",
        target_id=str(new_admin.id),
        details={"email": email, "tenant_id": tenant_id},
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=tenant_id,
        resource_type="admin_user",
        result="success",
    )

    await session.commit()
    await session.refresh(new_admin)

    return {"message": "CREATED", "admin": AdminUserPublic.model_validate(new_admin)}


@router.post("/seed")
async def seed_admin(session: AsyncSession = Depends(get_session)):
    # P0 safety: do not allow seeding in staging/prod.
    from config import settings
    if settings.env in {"prod", "staging"}:
        return {"message": "Seeding disabled in this environment"}

    try:
        from app.routes.tenant import seed_default_tenants
        await seed_default_tenants(session)
        
        stmt = select(AdminUser).where(AdminUser.email == "admin@casino.com")
        result = await session.execute(stmt)
        existing = result.scalars().first()
        
        if not existing:
            # Dev/local convenience seed only.
            # In staging/prod use BOOTSTRAP_OWNER_* env-based bootstrap.
            super_admin = AdminUser(
                email="admin@casino.com",
                username="superadmin",
                full_name="Super Owner",
                role="Super Admin",
                tenant_id="default_casino",
                is_platform_owner=True,
                password_hash=get_password_hash("Admin123!"),
                status="active"
            )
            session.add(super_admin)
            await session.commit()
            logger.info("Super Admin Seeded successfully.")
            return {"message": "Super Admin Seeded"}
        
        logger.info("Admin already exists, skipping seed.")
        return {"message": "Already seeded"}
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        # Don't crash startup if seed fails, just log
        return {"message": "Seeding failed", "error": str(e)}
