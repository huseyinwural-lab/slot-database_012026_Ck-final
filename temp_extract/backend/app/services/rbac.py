from __future__ import annotations

from fastapi import HTTPException

from app.models.sql_models import AdminUser


# Canonical roles for Player Ops RBAC
# NOTE: We normalize raw role strings to avoid "string drift" causing accidental 403s.
ROLE_SUPPORT = "Support"
ROLE_OPS = "Ops"
ROLE_ADMIN = "Admin"
ROLE_SUPER_ADMIN = "Super Admin"


def normalize_role(raw_role: str | None) -> str:
    r = (raw_role or "").strip()
    if not r:
        return ""

    key = r.replace("-", " ").replace("_", " ").strip().upper()

    # Admin aliases (treat Tenant Admin as ADMIN for P0 "least surprise")
    if key in {"TENANT ADMIN", "TENANTADMIN", "TENANT ADMINISTRATOR", "ADMIN", "ADMINISTRATOR"}:
        return ROLE_ADMIN

    # Ops aliases
    if key in {"OPS", "OPERATIONS", "OPERATION", "OP"}:
        return ROLE_OPS

    # Support aliases
    if key in {"SUPPORT", "CS", "CUSTOMER SUPPORT", "CUSTOMERSUPPORT"}:
        return ROLE_SUPPORT

    # Super admin aliases
    if key in {"SUPER ADMIN", "SUPERADMIN"}:
        return ROLE_SUPER_ADMIN

    # If unknown, keep original trimmed string
    return r


def canonical_role(admin: AdminUser) -> str:
    """Return the canonical role label used by RBAC."""

    return normalize_role(getattr(admin, "role", None))


def require_role_any(admin: AdminUser, allowed: set[str]) -> None:
    role = canonical_role(admin)

    # Super Admin / Owner override
    if role == ROLE_SUPER_ADMIN or getattr(admin, "is_platform_owner", False):
        return

    if role not in allowed:
        raise HTTPException(status_code=403, detail={"error_code": "FORBIDDEN"})


# Policy helpers

def require_support_view(admin: AdminUser) -> None:
    # Everyone with a role can view player audit/notes.
    require_role_any(admin, {ROLE_SUPPORT, ROLE_OPS, ROLE_ADMIN, ROLE_SUPER_ADMIN})


def require_ops(admin: AdminUser) -> None:
    require_role_any(admin, {ROLE_OPS, ROLE_ADMIN, ROLE_SUPER_ADMIN})


def require_admin(admin: AdminUser) -> None:
    require_role_any(admin, {ROLE_ADMIN, ROLE_SUPER_ADMIN})
