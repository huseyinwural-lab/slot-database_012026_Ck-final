from fastapi import Request

from app.models.sql_models import AdminUser


def get_current_tenant_id(request: Request, admin: AdminUser) -> str:
    """Aktif tenant_id'yi belirler.

    Öncelik sırası:
    1) (Sadece Platform Owner için) Header X-Tenant-ID (impersonation)
    2) admin.tenant_id
    3) "default_casino"

    Güvenlik: Platform owner olmayan bir kullanıcı X-Tenant-ID ile başka tenant verisine
    erişemez. Header yalnızca owner için dikkate alınır.
    """

    header_tenant = request.headers.get("X-Tenant-ID") if request else None
    if header_tenant and getattr(admin, "is_platform_owner", False):
        return header_tenant

    if getattr(admin, "tenant_id", None):
        return admin.tenant_id

    return "default_casino"
