from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.routes.auth_snippet import get_current_admin
from app.queue.arq_client import get_queue
from app.schemas.reconciliation import (
    ReconciliationRunCreate,
    ReconciliationRunOut,
    ReconciliationRunListResponse,
)
from app.services.reconciliation_runs import create_run, get_run, list_runs
from app.jobs.reconciliation_run_job import run_reconciliation_for_run_id

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


@router.post("/runs", response_model=ReconciliationRunOut)
async def create_reconciliation_run(
    payload: ReconciliationRunCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    run = await create_run(
        session,
        provider=payload.provider,
        window_start=payload.window_start,
        window_end=payload.window_end,
        dry_run=payload.dry_run,
        idempotency_key=payload.idempotency_key,
        created_by_admin_id=str(current_admin.id),
    )

    # Decide runner: queue (ARQ) vs background task fallback
    # For tests / dev we default to background to avoid needing Redis.
    try:
        from config import settings as app_settings  # type: ignore
        use_queue = getattr(app_settings, "recon_runner", "queue") == "queue"
    except Exception:  # pragma: no cover - config import fallback
        use_queue = False

    if use_queue:
        try:
            queue = get_queue()
            background_tasks.add_task(queue.enqueue_reconciliation_run, run.id)
        except RuntimeError:
            # Queue not initialised, fall back to in-process background task
            background_tasks.add_task(run_reconciliation_for_run_id, run.id)
    else:
        background_tasks.add_task(run_reconciliation_for_run_id, run.id)

    return ReconciliationRunOut(
        id=run.id,
        provider=run.provider,
        window_start=run.window_start,
        window_end=run.window_end,
        dry_run=run.dry_run,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        stats_json=run.stats_json,
        error_json=run.error_json,
    )


@router.get("/runs/{run_id}", response_model=ReconciliationRunOut)
async def get_reconciliation_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    run = await get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"error_code": "RUN_NOT_FOUND"})
    return ReconciliationRunOut(
        id=run.id,
        provider=run.provider,
        window_start=run.window_start,
        window_end=run.window_end,
        dry_run=run.dry_run,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        stats_json=run.stats_json,
        error_json=run.error_json,
    )


@router.get("/runs", response_model=ReconciliationRunListResponse)
async def list_reconciliation_runs(
    provider: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    runs, total = await list_runs(session, provider=provider, limit=limit, offset=offset)
    items = [
        ReconciliationRunOut(
            id=r.id,
            provider=r.provider,
            window_start=r.window_start,
            window_end=r.window_end,
            dry_run=r.dry_run,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            stats_json=r.stats_json,
            error_json=r.error_json,
        )
        for r in runs
    ]
    return ReconciliationRunListResponse(items=items, meta={"total": total, "limit": limit, "offset": offset})
