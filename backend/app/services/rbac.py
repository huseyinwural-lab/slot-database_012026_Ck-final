from __future__ import annotations

from fastapi import HTTPException

from app.models.sql_models import AdminUser


# Canonical roles for Player Ops RBAC
ROLE_SUPPORT = "Support"
ROLE_OPS = "Ops"
ROLE_ADMIN = "Admin"
ROLE_SUPER_ADMIN = "Super Admin"


def canonical_role(admin: AdminUser) -> str:
    """Return the canonical role label used by RBAC.

    Current codebase primarily uses AdminUser.role as a display string.
    """

    return (getattr(admin, "role", None) or "").strip()


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
