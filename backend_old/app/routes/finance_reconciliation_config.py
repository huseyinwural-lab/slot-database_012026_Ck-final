from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/finance/reconciliation", tags=["finance_reconciliation_config"])


# P0: store scheduler config in memory (per backend process).
# This is sufficient to make the UI functional without introducing DB migrations.
_SCHEDULE_BY_TENANT: Dict[str, Dict[str, Dict[str, Any]]] = {}


def _compute_next_run(frequency: str) -> Optional[str]:
    now = datetime.now(timezone.utc)
    freq = (frequency or "daily").lower()
    if freq == "hourly":
        nxt = now + timedelta(hours=1)
    elif freq == "weekly":
        nxt = now + timedelta(days=7)
    else:
        nxt = now + timedelta(days=1)
    return nxt.isoformat()


@router.get("/config")
async def get_reconciliation_config(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    tenant_cfg = _SCHEDULE_BY_TENANT.get(tenant_id, {})
    # Return array (ReconciliationPanel expects array)
    out: List[Dict[str, Any]] = []
    for provider, cfg in tenant_cfg.items():
        out.append(cfg)
    return out


@router.post("/config")
async def save_reconciliation_config(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    provider = (payload.get("provider") or "").strip()
    if not provider:
        raise HTTPException(status_code=400, detail={"error_code": "PROVIDER_REQUIRED"})

    frequency = (payload.get("frequency") or "daily").strip().lower()
    if frequency not in {"hourly", "daily", "weekly"}:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_FREQUENCY"})

    auto_fetch_enabled = bool(payload.get("auto_fetch_enabled"))

    cfg = {
        "provider": provider,
        "frequency": frequency,
        "auto_fetch_enabled": auto_fetch_enabled,
        "last_run": None,
        "next_run": _compute_next_run(frequency) if auto_fetch_enabled else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    _SCHEDULE_BY_TENANT.setdefault(tenant_id, {})[provider] = cfg
    return cfg


@router.post("/run-auto")
async def run_auto_match_now(
    request: Request,
    payload: Dict[str, Any] = Body(default={}),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """P0: deterministik mock run.

    UI expects a report-like object (provider_name, items, totals).
    We return a minimal deterministic shape and also update last_run/next_run.
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    provider = (payload.get("provider") or "Stripe").strip()

    cfg = _SCHEDULE_BY_TENANT.setdefault(tenant_id, {}).setdefault(
        provider,
        {
            "provider": provider,
            "frequency": "daily",
            "auto_fetch_enabled": False,
            "last_run": None,
            "next_run": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    now = datetime.now(timezone.utc)
    cfg["last_run"] = now.isoformat()
    if cfg.get("auto_fetch_enabled"):
        cfg["next_run"] = _compute_next_run(cfg.get("frequency") or "daily")

    # Minimal deterministic report object for UI
    report = {
        "id": f"mock_{provider.lower()}_{now.strftime('%Y%m%d%H%M%S')}",
        "provider_name": provider,
        "file_name": "Auto-Fetch",
        "period_start": (now - timedelta(days=1)).isoformat(),
        "period_end": now.isoformat(),
        "total_records": 3,
        "mismatches": 1,
        "fraud_alerts": 0,
        "currency_mismatches": 0,
        "status": "completed",
        "items": [
            {
                "id": "mock_item_1",
                "provider_ref": "psp_ref_001",
                "db_amount": 10.0,
                "provider_amount": 10.0,
                "difference": 0.0,
                "original_currency": "USD",
                "exchange_rate": 1.0,
                "converted_amount": 10.0,
                "status": "matched",
                "risk_flag": False,
                "notes": "OK",
            },
            {
                "id": "mock_item_2",
                "provider_ref": "psp_ref_002",
                "db_amount": 20.0,
                "provider_amount": 25.0,
                "difference": 5.0,
                "original_currency": "USD",
                "exchange_rate": 1.0,
                "converted_amount": 25.0,
                "status": "mismatch_amount",
                "risk_flag": False,
                "notes": "Amount mismatch",
            },
            {
                "id": "mock_item_3",
                "provider_ref": "psp_ref_003",
                "db_amount": None,
                "provider_amount": 15.0,
                "difference": 15.0,
                "original_currency": "USD",
                "exchange_rate": 1.0,
                "converted_amount": 15.0,
                "status": "missing_in_db",
                "risk_flag": False,
                "notes": "Missing in DB",
            },
        ],
        "created_at": now.isoformat(),
    }

    return report
