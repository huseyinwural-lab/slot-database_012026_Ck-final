from fastapi import Request
from app.models.domain.admin import AdminUser


def get_current_tenant_id(request: Request, admin: AdminUser) -> str:
    """Aktif tenant_id'yi belirler.

    Öncelik sırası:
    1) Header X-Tenant-ID
    2) admin.tenant_id
    3) "default_casino"
    """
    header_tenant = request.headers.get("X-Tenant-ID") if request else None
    if header_tenant:
        return header_tenant

    if getattr(admin, "tenant_id", None):
        return admin.tenant_id

    return "default_casino"
