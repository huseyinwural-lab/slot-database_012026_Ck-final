from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import AuditLog, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

@router.get("/events")
async def get_logs(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Logs are global for now, but should be scoped if needed
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    result = await session.execute(query)
    return result.scalars().all()
