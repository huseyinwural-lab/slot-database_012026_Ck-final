from __future__ import annotations

from typing import Any


from config import settings
from app.jobs.reconciliation_run_job import run_reconciliation_for_run_id


async def reconciliation_run_job(ctx: dict[str, Any], run_id: str) -> None:
    """ARQ worker function wrapping our reconciliation_run_job.

    ctx currently unused but kept for future logging/telemetry expansion.
    """

    await run_reconciliation_for_run_id(run_id)


class WorkerSettings:
    # List of functions this worker can execute
    functions = [reconciliation_run_job]

    # Redis connection
    redis_settings = settings.arq_redis_settings

    # Timeouts / retries (can be tuned via env-backed Settings later if needed)
    max_jobs = 10
    job_timeout = 300
    max_tries = 3
