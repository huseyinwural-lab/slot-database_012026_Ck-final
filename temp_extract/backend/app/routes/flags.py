from __future__ import annotations

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.services.feature_access import enforce_module_access
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/flags", tags=["flags"])


async def _enforce(request: Request, session: AsyncSession, admin: AdminUser):
    # Experiments/flags module is owner-only in catalog.
    require_owner(admin)
    tenant_id = await get_current_tenant_id(request, admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="experiments")


@router.get("/")
async def list_flags(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    await _enforce(request, session, current_admin)
    # Safe default: no flags configured.
    return []


@router.post("/")
async def create_flag(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await _enforce(request, session, current_admin)
    # Stub: accept payload, return ok.
    return {"message": "CREATED", "flag": payload}


@router.post("/{flag_id}/toggle")
async def toggle_flag(
    flag_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await _enforce(request, session, current_admin)
    return {"message": "TOGGLED", "flag_id": flag_id}


@router.get("/experiments")
async def list_experiments(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    await _enforce(request, session, current_admin)
    # Safe default: no experiments running.
    return []


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await _enforce(request, session, current_admin)
    return {"message": "STARTED", "experiment_id": experiment_id}


@router.post("/experiments/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await _enforce(request, session, current_admin)
    return {"message": "PAUSED", "experiment_id": experiment_id}


@router.get("/segments")
async def list_segments(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    await _enforce(request, session, current_admin)
    return []


@router.get("/audit-log")
async def audit_log(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    await _enforce(request, session, current_admin)
    return []


@router.get("/environment-comparison")
async def environment_comparison(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    await _enforce(request, session, current_admin)
    return []


@router.get("/groups")
async def list_groups(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[str]:
    await _enforce(request, session, current_admin)
    # UI default
    return ["Payments", "Risk", "CRM", "Affiliates"]


@router.post("/kill-switch")
async def flags_kill_switch(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Legacy endpoint used by FeatureFlags.jsx.

    Global kill switch for the platform is env-driven (KILL_SWITCH_ALL).
    This endpoint is kept as a no-op to keep the UI stable.
    """
    await _enforce(request, session, current_admin)
    return {"message": "OK"}
