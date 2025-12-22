from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reconciliation_run import ReconciliationRun


async def create_run(
    session: AsyncSession,
    *,
    provider: str,
    window_start,
    window_end,
    dry_run: bool,
    idempotency_key: Optional[str],
    created_by_admin_id: Optional[str] = None,
) -> ReconciliationRun:
    """Create a reconciliation run with optional idempotency.

    If idempotency_key is provided, we enforce uniqueness per (provider, idempotency_key)
    using a one-shot INSERT .. ON CONFLICT DO NOTHING followed by SELECT.
    """

    values: Dict[str, Any] = {
        "provider": provider,
        "window_start": window_start,
        "window_end": window_end,
        "dry_run": dry_run,
        "status": "queued",
        "idempotency_key": idempotency_key,
    }

    # Simple path: no idempotency key -> plain insert
    if not idempotency_key:
        run = ReconciliationRun(**values)
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run

    stmt = (
        insert(ReconciliationRun)
        .values(**values)
        .on_conflict_do_nothing(
            index_elements=[ReconciliationRun.provider, ReconciliationRun.idempotency_key]
        )
        .returning(ReconciliationRun)
    )

    result = await session.execute(stmt)
    inserted = result.scalar_one_or_none()
    if inserted is not None:
        await session.commit()
        return inserted

    # Conflict path: fetch existing
    query = select(ReconciliationRun).where(
        ReconciliationRun.provider == provider,
        ReconciliationRun.idempotency_key == idempotency_key,
    )
    existing = (await session.execute(query)).scalar_one()
    return existing


async def get_run(session: AsyncSession, run_id: str) -> Optional[ReconciliationRun]:
    return await session.get(ReconciliationRun, run_id)


async def list_runs(
    session: AsyncSession,
    *,
    provider: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[ReconciliationRun], int]:
    query = select(ReconciliationRun)
    if provider:
        query = query.where(ReconciliationRun.provider == provider)

    total_query = query.with_only_columns(ReconciliationRun.id).order_by(None)
    total = len((await session.execute(total_query)).scalars().all())

    query = query.order_by(ReconciliationRun.created_at.desc()).offset(offset).limit(limit)
    rows = (await session.execute(query)).scalars().all()
    return rows, total
