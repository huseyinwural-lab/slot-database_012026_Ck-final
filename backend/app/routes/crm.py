from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.services.feature_access import enforce_module_access

router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


# Stub returning array for CRM frontend
@router.get("/")
async def get_crm(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    await enforce_module_access(session=session, tenant_id=current_admin.tenant_id, module_key="crm")
    return []
