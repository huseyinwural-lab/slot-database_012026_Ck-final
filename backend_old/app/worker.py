from datetime import datetime, timedelta
from arq import cron
from app.core.database import get_session
from app.jobs.reconciliation_run_job import run_reconciliation_for_run_id
from app.models.reconciliation_run import ReconciliationRun
from app.services.metrics import metrics
from config import settings
import logging

logger = logging.getLogger(__name__)

async def startup(ctx):
    logger.info("Worker starting...")
    # Engine is initialized at module level in app.core.database
    logger.info("worker.db_engine_initialized", extra={"event": "worker.db_engine_initialized"})

async def shutdown(ctx):
    logger.info("Worker shutting down...")
    from app.core.database import engine
    if engine:
        await engine.dispose()

async def run_daily_reconciliation(ctx):
    """
    Cron job to run daily reconciliation for the previous day.
    """
    logger.info("Starting daily reconciliation cron job")
    
    # Define window (Yesterday 00:00 to 23:59:59)
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    window_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    providers = ["stripe", "adyen"]
    
    # We need to manually handle session since we are not in a request context
    async for session in get_session():
        for provider in providers:
            try:
                # Create Run Record
                run = ReconciliationRun(
                    provider=provider,
                    window_start=window_start,
                    window_end=window_end,
                    status="queued",
                    dry_run=False,
                    created_at=datetime.utcnow()
                )
                session.add(run)
                await session.commit()
                await session.refresh(run)
                
                # Run Logic
                # We can call the job directly since we are in the worker
                await run_reconciliation_for_run_id(run.id)
                
                # Check results for metrics
                await session.refresh(run)
                if run.stats_json:
                    findings = run.stats_json.get("total_findings", 0)
                    critical = run.stats_json.get("critical_findings", 0) # Assuming this field exists
                    metrics.record_reconciliation_result(findings, critical)
                    
                logger.info(f"Daily reconciliation for {provider} completed. Status: {run.status}")
                
            except Exception as e:
                logger.error(f"Failed daily reconciliation for {provider}: {e}")
        break # get_session is a generator, we just need one session context

class WorkerSettings:
    functions = [run_reconciliation_for_run_id]
    cron_jobs = [
        cron(run_daily_reconciliation, hour=2, minute=0) # Run at 2 AM UTC
    ]
    redis_settings = settings.arq_redis_settings
    on_startup = startup
    on_shutdown = shutdown
