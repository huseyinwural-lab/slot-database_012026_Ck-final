from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.constants.feature_catalog import FEATURE_CATALOG
from app.core.errors import AppError
from app.models.sql_models import Tenant
from config import settings


def _is_kill_switch_all_enabled() -> bool:
    raw = (getattr(settings, "kill_switch_all", None) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


async def enforce_module_access(
    *,
    session: AsyncSession,
    tenant_id: str,
    module_key: str,
) -> None:
    """Enforce module access rules (global kill switch + tenant kill switch + feature flag).

    Order:
    1) Global kill switch (ENV: KILL_SWITCH_ALL=true) => 503 for non-core modules
    2) Tenant kill switch (tenant.features.kill_switches[module_key] == true) => 503
    3) Feature flag (tenant.features[required_flag] == true) => 403
    """

    mod = FEATURE_CATALOG.get(module_key)
    if not mod:
        # Unknown module keys should be treated as not found in code.
        raise HTTPException(status_code=404, detail={"error_code": "MODULE_NOT_FOUND", "module": module_key})

    # 1) Global kill switch
    if mod.non_core and _is_kill_switch_all_enabled():
        raise AppError(
            error_code="MODULE_DISABLED",
            message="Module disabled",
            status_code=503,
            details={"module": module_key, "reason": "global_kill_switch"},
        )

    res = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = res.scalars().first()
    features = (tenant.features if tenant else {}) or {}

    # 2) Tenant kill switch
    kill_switches = (features.get("kill_switches") or {}) if isinstance(features, dict) else {}
    if kill_switches.get(module_key) is True:
        raise AppError(
            error_code="MODULE_DISABLED",
            message="Module disabled",
            status_code=503,
            details={"module": module_key, "tenant_id": tenant_id, "reason": "tenant_kill_switch"},
        )

    # 3) Feature flag
    flag = mod.required_flag
    if features.get(flag) is not True:
        raise AppError(
            error_code="FEATURE_DISABLED",
            message="Feature is disabled for this tenant",
            status_code=403,
            details={"feature": flag, "module": module_key},
        )
