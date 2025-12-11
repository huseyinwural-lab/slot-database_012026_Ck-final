from fastapi import Request, HTTPException
from app.models.domain.admin import AdminUser
from app.utils.tenant import get_current_tenant_id
from app.routes.core import get_db


async def ensure_tenant_feature(request: Request, admin: AdminUser, feature_key: str):
    """Belirli bir tenant feature'ının açık olduğunu garanti eder.

    Aksi durumda 403 TENANT_FEATURE_DISABLED fırlatır.
    """
    db = get_db()
    tenant_id = get_current_tenant_id(request, admin)
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "features": 1})
    if not tenant:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_NOT_FOUND", "tenant_id": tenant_id},
        )

    features = tenant.get("features") or {}
    if not features.get(feature_key, False):
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_FEATURE_DISABLED", "feature": feature_key},
        )
