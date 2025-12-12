"""
Permission and role checking utilities
"""
from app.models.domain.admin import AdminUser
from fastapi import HTTPException


def is_owner(admin: AdminUser) -> bool:
    """
    Check if admin is platform owner (can see all tenants)
    
    Owner criteria:
    - is_platform_owner = True
    - OR role = "Super Admin"
    """
    return admin.is_platform_owner or admin.role == "Super Admin"


def require_owner(admin: AdminUser):
    """
    Raise 403 if admin is not owner
    Use this as a guard for owner-only endpoints
    """
    if not is_owner(admin):
        raise HTTPException(
            status_code=403,
            detail="Owner access only. This endpoint requires platform owner privileges."
        )


def get_tenant_filter(admin: AdminUser) -> dict:
    """
    Return MongoDB filter for tenant scoping
    
    - Owner: No filter (can see all)
    - Tenant: Filter by tenant_id
    """
    if is_owner(admin):
        return {}
    
    return {"tenant_id": admin.tenant_id}
