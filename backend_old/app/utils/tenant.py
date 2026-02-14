"""Deprecated wrapper.

P0-TENANT-SCOPE: tenant context resolution moved to app.core.tenant_context.
Keep this module to avoid changing all imports at once.
"""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_context import get_current_tenant_id as _get_current_tenant_id
from app.models.sql_models import AdminUser


async def get_current_tenant_id(
    request: Request,
    admin: AdminUser,
    session: AsyncSession | None = None,
) -> str:
    return await _get_current_tenant_id(request=request, current_admin=admin, session=session)
