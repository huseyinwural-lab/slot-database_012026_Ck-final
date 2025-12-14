from fastapi import APIRouter, Depends, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import FeatureFlag
from app.utils.auth import get_current_admin, AdminUser
from app.services.feature_access import enforce_module_access
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/features", tags=["features"])


@router.get("/", response_model=List[FeatureFlag])
async def get_feature_flags(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="experiments")

    query = select(FeatureFlag)
    result = await session.execute(query)
    return result.scalars().all()
