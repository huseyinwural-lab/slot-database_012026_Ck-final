from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, text
from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from config import settings
from datetime import datetime
import os

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])

@router.get("/health", response_model=dict)
async def ops_health_check(
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Detailed Ops Health Check (P0 for Go-Live)."""
    
    health = {
        "status": "green",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # 1. Database
    try:
        await session.execute(text("SELECT 1"))
        health["components"]["database"] = {"status": "ok", "latency_ms": 0} # simplified
    except Exception as e:
        health["components"]["database"] = {"status": "error", "error": str(e)}
        health["status"] = "red"

    # 2. Migrations (Check for alembic table)
    try:
        res = await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        version = res.scalar()
        health["components"]["migrations"] = {"status": "ok", "version": version}
    except Exception:
        health["components"]["migrations"] = {"status": "unknown", "error": "Table not found"}
        # Warning only, don't red-flag unless strict

    # 3. Audit Chain (Check last event hash)
    try:
        res = await session.execute(text("SELECT row_hash, sequence, timestamp FROM auditevent ORDER BY sequence DESC LIMIT 1"))
        last = res.mappings().first()
        if last:
            health["components"]["audit_chain"] = {
                "status": "ok", 
                "head_sequence": last['sequence'],
                "head_hash": last['row_hash'][:8] + "...",
                "last_event_time": last['timestamp']
            }
        else:
            health["components"]["audit_chain"] = {"status": "empty"}
    except Exception as e:
        health["components"]["audit_chain"] = {"status": "error", "error": str(e)}
        health["status"] = "red"

    # 4. Engine Standards (Task D4 Extension)
    try:
        from app.models.engine_models import EngineStandardProfile
        res = await session.execute(select(EngineStandardProfile))
        profiles = res.scalars().all()
        health["components"]["engine_standards"] = {
            "status": "ok" if len(profiles) >= 3 else "warning",
            "loaded_count": len(profiles)
        }
    except Exception as e:
        health["components"]["engine_standards"] = {"status": "error", "error": str(e)}

    # 4. Storage (Check reachability)
    # Check if local path exists or S3 creds are present
    storage_status = "ok"
    if settings.audit_archive_backend == "filesystem":
        if not os.path.exists(settings.audit_archive_path):
            storage_status = "warning (path missing)"
    elif settings.audit_archive_backend == "s3":
        if not settings.audit_s3_bucket:
            storage_status = "error (config missing)"
            health["status"] = "red"
            
    health["components"]["storage"] = {
        "backend": settings.audit_archive_backend,
        "status": storage_status
    }

    return health
