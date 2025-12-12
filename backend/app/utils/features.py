import logging
from fastapi import Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.domain.admin import AdminUser
from app.utils.tenant import get_current_tenant_id


logger = logging.getLogger("app.features")


async def ensure_tenant_feature(request: Request, admin: AdminUser, feature_key: str, db: AsyncIOMotorDatabase):
    """Ensure that a given tenant feature flag is enabled.

    If not, raises 403 TENANT_FEATURE_DISABLED and logs a structured warning
    with correlation id, tenant id and admin id.
    """
    tenant_id = get_current_tenant_id(request, admin)
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "features": 1})
    request_id = request.headers.get("X-Request-ID")

    if not tenant:
        logger.warning(
            "tenant_not_found_for_feature",
            extra={
                "tenant_id": tenant_id,
                "admin_id": admin.id,
                "feature": feature_key,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_NOT_FOUND", "tenant_id": tenant_id},
        )

    features = tenant.get("features") or {}
    if not features.get(feature_key, False):
        logger.warning(
            "tenant_feature_denied",
            extra={
                "tenant_id": tenant_id,
                "admin_id": admin.id,
                "feature": feature_key,
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_FEATURE_DISABLED", "feature": feature_key},
        )


async def ensure_tenant_feature_by_tenant_id(tenant_id: str, feature_key: str, request_id: str | None = None):
    """Ensure feature flag for non-admin contexts (e.g. API key / robot).

    Used when we only have tenant_id (no AdminUser/Request), for example
    in the Game Robot orchestrator.
    """
    db = get_db()
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "features": 1})
    if not tenant:
        logger.warning(
            "tenant_not_found_for_feature",
            extra={
                "tenant_id": tenant_id,
                "admin_id": None,
                "feature": feature_key,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_NOT_FOUND", "tenant_id": tenant_id},
        )

    features = tenant.get("features") or {}
    if not features.get(feature_key, False):
        logger.warning(
            "tenant_feature_denied",
            extra={
                "tenant_id": tenant_id,
                "admin_id": None,
                "feature": feature_key,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_FEATURE_DISABLED", "feature": feature_key},
        )
