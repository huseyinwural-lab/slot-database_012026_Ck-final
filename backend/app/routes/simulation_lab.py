from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.errors import AppError
from app.models.simulation_sql import SimulationRun
from app.services.audit import audit
from app.utils.auth import get_current_admin, AdminUser
from app.utils.tenant import get_current_tenant_id


router = APIRouter(prefix="/api/v1/simulation-lab", tags=["simulation_lab"])


def _request_meta(request: Request) -> Dict[str, Any]:
    return {
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        "ip_address": getattr(request.state, "ip_address", None),
        "user_agent": getattr(request.state, "user_agent", None),
    }


async def _audit_best_effort(
    *,
    session: AsyncSession,
    request: Request,
    admin: AdminUser,
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None,
    result: str,
    status: str,
    details: Dict[str, Any] | None = None,
) -> None:
    try:
        meta = _request_meta(request)
        await audit.log_event(
            session=session,
            request_id=meta["request_id"],
            actor_user_id=str(admin.id),
            actor_role=getattr(admin, "role", None),
            tenant_id=str(tenant_id),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            status=status,
            reason=request.headers.get("X-Reason"),
            ip_address=meta["ip_address"],
            user_agent=meta["user_agent"],
            details=details or {},
        )
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass


@router.get("/runs")
async def list_runs(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = (
        select(SimulationRun)
        .where(SimulationRun.tenant_id == tenant_id)
        .order_by(SimulationRun.created_at.desc())
        .limit(200)
    )
    rows = (await session.execute(stmt)).scalars().all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "simulation_type": r.simulation_type,
            "status": r.status,
            "created_by": r.created_by,
            "notes": r.notes,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/runs")
async def create_run(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    run_id = (payload.get("id") or str(uuid.uuid4())).strip()
    name = (payload.get("name") or "Simulation Run").strip()
    simulation_type = (payload.get("simulation_type") or "mixed").strip()
    status = (payload.get("status") or "draft").strip()
    created_by = (payload.get("created_by") or current_admin.email or "admin").strip()
    notes = payload.get("notes")

    # Upsert semantics: if exists, ignore (idempotent-ish)
    stmt = select(SimulationRun).where(SimulationRun.id == run_id, SimulationRun.tenant_id == tenant_id)
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        return {"id": existing.id}

    run = SimulationRun(
        id=run_id,
        tenant_id=tenant_id,
        name=name,
        simulation_type=simulation_type,
        status=status,
        created_by=created_by,
        notes=notes,
        created_at=datetime.utcnow(),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    await _audit_best_effort(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="simulation.run.created",
        resource_type="simulation_run",
        resource_id=run.id,
        result="success",
        status="SUCCESS",
        details={"simulation_type": simulation_type},
    )

    return {"id": run.id}


@router.post("/game-math")
async def run_game_math(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # MVP: return deterministic results for UI.
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    run_id = (payload.get("run_id") or "unknown").strip()

    await _audit_best_effort(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="simulation.game_math.executed",
        resource_type="simulation_run",
        resource_id=run_id,
        result="success",
        status="SUCCESS",
    )

    spins = int(payload.get("spins_to_simulate") or 10000)
    rtp = float(payload.get("rtp_override") or 96.5)

    # Simple deterministic derived metrics
    expected_return = spins * (rtp / 100.0)

    return {
        "run_id": run_id,
        "spins": spins,
        "rtp": rtp,
        "expected_return": expected_return,
        "variance": 0.0,
        "status": "completed",
    }
