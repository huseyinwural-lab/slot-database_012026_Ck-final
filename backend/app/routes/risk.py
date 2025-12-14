from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import RiskRule, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])

@router.get("/rules")
async def get_risk_rules(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(RiskRule).where(RiskRule.tenant_id == current_admin.tenant_id)
    result = await session.execute(query)
    # Direct list return
    return result.scalars().all()
