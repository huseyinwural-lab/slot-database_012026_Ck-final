import asyncio
import sys
import os
import logging
from datetime import datetime, timezone, timedelta

# Path
sys.path.append("/app/scripts")
sys.path.append("/app/backend")

# Import all models to ensure registry is populated
from app.models import sql_models, game_models, robot_models

from audit_archive_export import export_audit_log
from purge_audit_logs import purge_audit_logs
from config import settings
from app.services.audit import audit
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cron_simulation")

DATABASE_URL = settings.database_url

async def run_cron_simulation():
    print("--- Starting Cron Simulation (D3) ---")
    
    # Create Engine/Session for logging the job execution
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 1. Archive Job (Yesterday)
    target_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Running Archive for {target_date}...")
    
    status = "SUCCESS"
    try:
        await export_audit_log(target_date)
    except Exception as e:
        status = "FAILED"
        print(f"Archive failed: {e}")

    # Log Job
    async with async_session() as session:
        # We need a system admin user context usually, but log_event takes raw IDs.
        # Use system/cron ID.
        await audit.log_event(
            session=session,
            request_id="cron-archive-sim",
            actor_user_id="system-cron",
            tenant_id="system",
            action="CRON_ARCHIVE_RUN",
            resource_type="cron_job",
            resource_id=target_date,
            result=status.lower(),
            status=status,
            reason="Daily Schedule",
            details={"job": "audit_archive_export", "date": target_date}
        )
        await session.commit()

    # 2. Purge Job
    print("Running Purge...")
    status = "SUCCESS"
    try:
        # Keep 90 days
        await purge_audit_logs(keep_days=90, dry_run=True) # Dry run for safety in simulation
    except Exception as e:
        status = "FAILED"
        print(f"Purge failed: {e}")

    # Log Job
    async with async_session() as session:
        await audit.log_event(
            session=session,
            request_id="cron-purge-sim",
            actor_user_id="system-cron",
            tenant_id="system",
            action="CRON_PURGE_RUN",
            resource_type="cron_job",
            resource_id="audit_purge",
            result=status.lower(),
            status=status,
            reason="Daily Schedule",
            details={"job": "purge_audit_logs", "dry_run": True}
        )
        await session.commit()

    await engine.dispose()
    print("--- Cron Simulation Complete ---")

if __name__ == "__main__":
    asyncio.run(run_cron_simulation())
