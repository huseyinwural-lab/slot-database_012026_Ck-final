from __future__ import annotations

from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser, Tenant
from app.utils.auth import get_current_admin
from app.utils.permissions import require_owner
from app.services.feature_access import enforce_module_access
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/kill-switch", tags=["kill_switch"])


@router.get("/status")
async def get_kill_switch_status(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # owner-only module
    require_owner(current_admin)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="kill_switch")

    tenant = await session.get(Tenant, tenant_id)
    features = (tenant.features if tenant else {}) or {}
    return {
        "kill_switch_all": False,  # global status is checked server-side; exposing exact value is optional
        "tenant_kill_switches": features.get("kill_switches") or {},
    }


@router.post("/tenant")
async def set_tenant_kill_switch(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Owner-only: update tenant.features.kill_switches[module_key]"""
    require_owner(current_admin)
    owner_tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=owner_tenant_id, module_key="kill_switch")

    tenant_id = payload.get("tenant_id")
    module_key = payload.get("module_key")
    disabled = payload.get("disabled")

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        return {"message": "TENANT_NOT_FOUND"}

    # Old state
    before_features = dict(tenant.features or {})
    before_kill_switches = dict(before_features.get("kill_switches", {}) or {})
    old_state = bool(before_kill_switches.get(module_key) is True)

    # New state
    new_state = bool(disabled)
    after_features = dict(before_features)
    kill_switches = dict(before_kill_switches)
    kill_switches[module_key] = new_state
    after_features["kill_switches"] = kill_switches

    # Use update statement to ensure the JSON field is properly updated
    from sqlalchemy import update
    stmt = update(Tenant).where(Tenant.id == tenant_id).values(features=after_features)
    await session.execute(stmt)

    # Audit (KS-P0-05)
    from app.services.audit import audit
    await audit.log(
        admin=current_admin,
        action="kill_switch.tenant.updated",
        module="kill_switch",
        target_id=str(tenant_id),
        details={
            "tenant_id": tenant_id,
            "module": module_key.upper() if isinstance(module_key, str) else module_key,
            "old_state": old_state,
            "new_state": new_state,
        },
        session=session,
        request_id=getattr(request.state, "request_id", None),
        tenant_id=str(tenant_id),
        resource_type="tenant",
        result="success",
    )

    await session.commit()

    return {"message": "UPDATED", "tenant_id": tenant_id, "kill_switches": kill_switches}
