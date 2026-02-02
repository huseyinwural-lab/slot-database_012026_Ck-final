from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.jobs.reconcile_psp import reconcile_mockpsp_vs_ledger
from app.models.reconciliation_run import ReconciliationRun


async def run_reconciliation_for_run_id(run_id: str) -> None:
    """Background job to execute a reconciliation run.

    This is a minimal implementation using a fresh AsyncSession.
    It updates the ReconciliationRun row status and stats_json/error_json fields.
    """

    async for session in get_session():  # get_session is async generator dependency
        await _execute_run(session, run_id)
        break


async def _execute_run(session: AsyncSession, run_id: str) -> None:
    run = await session.get(ReconciliationRun, run_id)
    if not run:
        return

    # Mark as running
    run.status = "running"
    run.updated_at = datetime.utcnow()
    session.add(run)
    await session.commit()

    started_at = datetime.utcnow()
    stats: Dict[str, Any] = {}

    try:
        # For now we only support mockpsp and a global reconciliation (tenant_id=None)
        await reconcile_mockpsp_vs_ledger(session, tenant_id=None, provider=run.provider)

        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        # Minimal stats: just duration for now; counts can be added later from job internals
        stats = {"duration_ms": duration_ms}

        run.status = "completed"
        run.stats_json = stats
        run.updated_at = finished_at
        session.add(run)
        await session.commit()

    except Exception as exc:  # pragma: no cover - defensive
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        run.status = "failed"
        run.error_json = {
            "reason": "job_exception",
            "message": str(exc),
            "duration_ms": duration_ms,
        }
        run.updated_at = finished_at
        session.add(run)
        await session.commit()
