from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AuditLog, AdminUser
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

@router.get("/events")
async def get_logs(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    result = await session.execute(query)
    # Direct list return
    return result.scalars().all()

# Stub endpoints returning empty lists (Frontend expects arrays for these)
@router.get("/cron")
async def get_cron_logs(): return []

@router.get("/health")
async def get_health_logs(): return []

@router.get("/deployments")
async def get_deployment_logs(): return []

@router.get("/config")
async def get_config_logs(): return []

@router.get("/errors")
async def get_error_logs(): return []

@router.get("/queues")
async def get_queue_logs(): return []

@router.get("/db")
async def get_db_logs(): return []

@router.get("/cache")
async def get_cache_logs(): return []

@router.get("/archive")
async def get_archive_logs(): return []
