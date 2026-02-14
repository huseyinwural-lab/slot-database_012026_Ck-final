import logging

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.sql_models import AdminUser, Tenant
from app.utils.tenant import get_current_tenant_id

logger = logging.getLogger("app.features")


async def ensure_tenant_feature(
    request: Request,
    admin: AdminUser,
    feature_key: str,
    session: AsyncSession,
):
    """Tenant feature flag kontrolü (SQLModel).

    Tenant id önceliği:
    1) X-Tenant-ID header
    2) admin.tenant_id
    3) default_casino
    """

    tenant_id = await get_current_tenant_id(request, admin, session=session)
    request_id = request.headers.get("X-Request-ID")

    res = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalars().first()

    if not tenant:
        logger.warning(
            "tenant_not_found_for_feature",
            extra={
                "tenant_id": tenant_id,
                "admin_id": getattr(admin, "id", None),
                "feature": feature_key,
                "request_id": request_id,
            },
        )
        raise HTTPException(status_code=403, detail={"error_code": "TENANT_NOT_FOUND", "tenant_id": tenant_id})

    features = tenant.features or {}
    if not features.get(feature_key, False):
        logger.warning(
            "tenant_feature_denied",
            extra={
                "tenant_id": tenant_id,
                "admin_id": getattr(admin, "id", None),
                "feature": feature_key,
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )
        raise HTTPException(status_code=403, detail={"error_code": "TENANT_FEATURE_DISABLED", "feature": feature_key})


async def ensure_tenant_feature_by_tenant_id(
    tenant_id: str,
    feature_key: str,
    session: AsyncSession,
    request_id: str | None = None,
):
    """Request/Admin olmayan yerlerde tenant feature kontrolü (SQLModel).

    Örn: API key / robot gibi servis context'lerinde.
    """

    res = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalars().first()

    if not tenant:
        logger.warning(
            "tenant_not_found_for_feature",
            extra={"tenant_id": tenant_id, "admin_id": None, "feature": feature_key, "request_id": request_id},
        )
        raise HTTPException(status_code=403, detail={"error_code": "TENANT_NOT_FOUND", "tenant_id": tenant_id})

    features = tenant.features or {}
    if not features.get(feature_key, False):
        logger.warning(
            "tenant_feature_denied",
            extra={"tenant_id": tenant_id, "admin_id": None, "feature": feature_key, "request_id": request_id},
        )
        raise HTTPException(status_code=403, detail={"error_code": "TENANT_FEATURE_DISABLED", "feature": feature_key})
