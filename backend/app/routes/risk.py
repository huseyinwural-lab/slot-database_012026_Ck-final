from fastapi import APIRouter, Depends, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import RiskRule, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])

@router.get("/rules")
async def get_risk_rules(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(RiskRule).where(RiskRule.tenant_id == tenant_id)
    result = await session.execute(query)
    # Direct list return
    return result.scalars().all()
