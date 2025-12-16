"""
Permission and role checking utilities
"""
from app.models.domain.admin import AdminUser, TenantRole
from fastapi import HTTPException, Depends
from app.utils.auth import get_current_admin


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


def require_tenant_role(allowed_roles: list[str]):
    """
    Factory to create a dependency for checking tenant roles.
    Usage: Depends(require_tenant_role(["tenant_admin", "finance"]))
    """
    def check_role(admin: AdminUser = Depends(get_current_admin)):
        # Platform owners bypass tenant role checks
        if is_owner(admin):
            return admin

        # If user has no specific tenant role, assume they are restricted unless they are full tenant admin
        user_role = admin.tenant_role or TenantRole.TENANT_ADMIN
        
        # "tenant_admin" is the super-admin of the tenant, access to everything within tenant
        if user_role == TenantRole.TENANT_ADMIN:
            return admin
            
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required one of: {allowed_roles}"
            )
        return admin
    return check_role


def get_tenant_filter(admin: AdminUser) -> dict:
    """Tenant scope filtresi.

    Not: Bu proje MongoDB'den PostgreSQL/SQLModel'e taşındı.
    Bu fonksiyon artık sadece "tenant_id" bazlı genel bir filtre sözlüğü döndürür.

    - Owner: boş filtre (tüm tenant'lar)
    - Tenant: tenant_id filtresi
    """
    if is_owner(admin):
        return {}
    
    return {"tenant_id": admin.tenant_id}
