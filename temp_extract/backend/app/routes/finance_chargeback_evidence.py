from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.sql_models import ChargebackCase, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/finance/chargebacks", tags=["finance_chargeback_evidence"])


@router.post("/{case_id}/evidence")
async def add_chargeback_evidence(
    case_id: str,
    request: Request,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """P0: Minimal endpoint so UI isn't a no-op.

    For now we accept a file_url and append it to evidence_files.
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    file_url = (payload.get("file_url") or "").strip()
    if not file_url:
        raise HTTPException(status_code=400, detail={"error_code": "FILE_URL_REQUIRED"})

    stmt = select(ChargebackCase).where(ChargebackCase.id == case_id, ChargebackCase.tenant_id == tenant_id)
    cb = (await session.execute(stmt)).scalars().first()
    if not cb:
        raise HTTPException(status_code=404, detail={"error_code": "CASE_NOT_FOUND"})

    cb.evidence_files = list(cb.evidence_files or [])
    cb.evidence_files.append(file_url)

    # best-effort updated_at if present
    if hasattr(cb, "updated_at"):
        setattr(cb, "updated_at", datetime.now(timezone.utc))

    session.add(cb)
    await session.commit()
    await session.refresh(cb)

    return {"status": "ok", "case": cb}
