from __future__ import annotations

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import AppError
from app.models.sql_models import Tenant, AdminUser


def _get_header_tenant_id(request: Request | None) -> str | None:
    if not request:
        return None
    raw = request.headers.get("X-Tenant-ID")
    return raw.strip() if raw and raw.strip() else None


async def get_current_tenant_id(
    request: Request,
    current_admin: AdminUser,
    session: AsyncSession | None = None,
) -> str:
    """Resolve active tenant scope.

    Rules (P0-TENANT-SCOPE):
    - Header name: X-Tenant-ID
    - Owner (is_platform_owner=True): may impersonate via header.
      - If header provided but invalid/unresolvable -> 400 INVALID_TENANT_HEADER
      - If no header -> default to current_admin.tenant_id
    - Tenant admin: header usage is forbidden.
      - If tenant admin sends header -> 403 TENANT_HEADER_FORBIDDEN
      - Else -> current_admin.tenant_id

    Notes:
    - Tenant IDs in this codebase are strings (may be UUIDs or slugs). "Invalid" means
      the tenant cannot be resolved in DB (when session is provided).
    """

    header_tenant = _get_header_tenant_id(request)

    # Tenant admin attempting to inject header is a policy violation.
    if header_tenant and not bool(getattr(current_admin, "is_platform_owner", False)):
        raise AppError(
            error_code="TENANT_HEADER_FORBIDDEN",
            message="X-Tenant-ID is only allowed for owner impersonation",
            status_code=403,
        )

    # Owner impersonation
    if header_tenant and bool(getattr(current_admin, "is_platform_owner", False)):
        if session is not None:
            stmt = select(Tenant.id).where(Tenant.id == header_tenant)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                raise AppError(
                    error_code="INVALID_TENANT_HEADER",
                    message="Invalid X-Tenant-ID",
                    status_code=400,
                )
        return header_tenant

    # Default deterministic scope
    return getattr(current_admin, "tenant_id", None) or "default_casino"
