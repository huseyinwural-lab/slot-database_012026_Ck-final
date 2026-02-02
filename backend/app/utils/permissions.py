from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import AppError
from app.models.sql_models import AdminUser, Tenant
from app.services.rbac import ROLE_ADMIN, ROLE_OPS, ROLE_SUPPORT, ROLE_SUPER_ADMIN, normalize_role
from app.utils.auth import get_current_admin

def require_owner(admin: AdminUser):
    if not admin.is_platform_owner:
        raise AppError("FORBIDDEN", "Platform Owner access required", 403)


def require_ops(admin: AdminUser):
    # Ops/Admin/Super Admin/Owner are allowed
    if admin.role not in {"Ops", "Admin", "Super Admin"} and not admin.is_platform_owner:
        raise AppError("FORBIDDEN", "Ops access required", 403)


def require_admin(admin: AdminUser):
    # Admin/Super Admin/Owner are allowed
    if admin.role not in {"Admin", "Super Admin"} and not admin.is_platform_owner:
        raise AppError("FORBIDDEN", "Admin access required", 403)


def require_support_view(admin: AdminUser):
    if admin.role not in {"Support", "Ops", "Admin", "Super Admin"} and not admin.is_platform_owner:
        raise AppError("FORBIDDEN", "Support view access required", 403)

async def require_feature(feature_key: str, admin: AdminUser, session: AsyncSession):
    """
    Core Logic to check if a feature is enabled for the admin's tenant.
    """
    # Platform owner usually bypasses or has all features? 
    # Better to enforce tenant config even for owner to simulate correctly.
    
    tenant = await session.get(Tenant, admin.tenant_id)
    if not tenant:
        raise AppError("TENANT_NOT_FOUND", "Tenant not found", 404)
        
    features = tenant.features or {}
    if not features.get(feature_key, False):
        raise AppError(
            error_code="FEATURE_DISABLED", 
            message=f"Feature '{feature_key}' is disabled for this tenant.", 
            status_code=403
        )

# Dependency Factory
def feature_required(feature_key: str):
    async def dependency(
        admin: AdminUser = Depends(get_current_admin),
        session: AsyncSession = Depends(get_session)
    ):
        await require_feature(feature_key, admin, session)
        return admin
    return dependency
