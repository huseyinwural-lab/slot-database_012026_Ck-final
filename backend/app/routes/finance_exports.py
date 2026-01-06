from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.sql_models import Transaction, AdminUser, ReconciliationReport, ChargebackCase
from app.services.csv_export import dicts_to_csv_bytes
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/finance", tags=["finance_exports"])


def _csv_response(content: bytes, filename_prefix: str) -> StreamingResponse:
    filename = f"{filename_prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


@router.get("/transactions/export")
async def export_finance_transactions(
    request: Request,
    type: Optional[str] = None,
    status: Optional[str] = None,
    player_search: Optional[str] = None,
    provider: Optional[str] = None,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    currency: Optional[str] = None,
    ip_address: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Transaction).where(Transaction.tenant_id == tenant_id)

    if type and type != "all":
        stmt = stmt.where(Transaction.type == type)
    if status and status != "all":
        stmt = stmt.where(Transaction.status == status)
    if provider and provider != "all":
        stmt = stmt.where(Transaction.provider == provider)
    if currency and currency != "all":
        stmt = stmt.where(Transaction.currency == currency)

    # P0: player_search/country/ip_address are not first-class columns; treat them as best-effort (tx-scoped).
    if player_search:
        like = f"%{player_search.strip()}%"
        stmt = stmt.where(
            (Transaction.id.ilike(like))
            | (Transaction.player_id.ilike(like))
            | (Transaction.provider_tx_id.ilike(like))
            | (Transaction.provider_event_id.ilike(like))
        )

    # Date filters
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            if sd.tzinfo is None:
                sd = sd.replace(tzinfo=timezone.utc)
            stmt = stmt.where(Transaction.created_at >= sd)
        except Exception:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            if ed.tzinfo is None:
                ed = ed.replace(tzinfo=timezone.utc)
            stmt = stmt.where(Transaction.created_at <= ed)
        except Exception:
            pass

    stmt = stmt.order_by(Transaction.created_at.desc()).limit(5000)
    rows = (await session.execute(stmt)).scalars().all()

    out: List[Dict[str, Any]] = []
    for tx in rows:
        out.append(
            {
                "id": tx.id,
                "player_id": tx.player_id,
                "type": tx.type,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "status": tx.status,
                "state": tx.state,
                "provider": tx.provider or "",
                "provider_tx_id": tx.provider_tx_id or "",
                "provider_event_id": tx.provider_event_id or "",
                "method": tx.method or "",
                "created_at": tx.created_at.isoformat() if tx.created_at else "",
            }
        )

    fieldnames = [
        "id",
        "player_id",
        "type",
        "amount",
        "currency",
        "status",
        "state",
        "provider",
        "provider_tx_id",
        "provider_event_id",
        "method",
        "created_at",
    ]

    return _csv_response(dicts_to_csv_bytes(out, fieldnames=fieldnames), "finance_transactions")


@router.get("/reports/export")
async def export_finance_reports(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    currency: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # Use the same aggregation logic as /finance/reports by importing the function.
    from app.routes.finance_reports import get_finance_reports

    report = await get_finance_reports(
        request=request,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        session=session,
        current_admin=current_admin,
    )

    # Flatten: one row summary + daily stats rows
    summary_row = {
        "metric": "summary",
        "ggr": report.get("ggr"),
        "ngr": report.get("ngr"),
        "total_deposit": report.get("total_deposit"),
        "total_withdrawal": report.get("total_withdrawal"),
        "bonus_cost": report.get("bonus_cost"),
        "provider_cost": report.get("provider_cost"),
        "payment_fees": report.get("payment_fees"),
        "chargeback_amount": report.get("chargeback_amount"),
        "chargeback_count": report.get("chargeback_count"),
        "fx_impact": report.get("fx_impact"),
    }

    out: List[Dict[str, Any]] = [summary_row]

    for d in report.get("daily_stats", []) or []:
        out.append(
            {
                "metric": "daily",
                "date": d.get("date"),
                "deposits": d.get("deposits"),
                "withdrawals": d.get("withdrawals"),
            }
        )

    fieldnames = [
        "metric",
        "date",
        "deposits",
        "withdrawals",
        "ggr",
        "ngr",
        "total_deposit",
        "total_withdrawal",
        "bonus_cost",
        "provider_cost",
        "payment_fees",
        "chargeback_amount",
        "chargeback_count",
        "fx_impact",
    ]

    return _csv_response(dicts_to_csv_bytes(out, fieldnames=fieldnames), "finance_reports")


@router.get("/reconciliation/export")
async def export_reconciliation(
    request: Request,
    provider: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(ReconciliationReport).where(ReconciliationReport.tenant_id == tenant_id)
    if provider:
        stmt = stmt.where(ReconciliationReport.provider_name == provider)

    stmt = stmt.order_by(ReconciliationReport.created_at.desc()).limit(5000)
    rows = (await session.execute(stmt)).scalars().all()

    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "provider_name": r.provider_name,
                "period_start": r.period_start.isoformat() if r.period_start else "",
                "period_end": r.period_end.isoformat() if r.period_end else "",
                "total_records": r.total_records,
                "mismatches": r.mismatches,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
        )

    fieldnames = [
        "id",
        "provider_name",
        "period_start",
        "period_end",
        "total_records",
        "mismatches",
        "status",
        "created_at",
    ]

    return _csv_response(dicts_to_csv_bytes(out, fieldnames=fieldnames), "finance_reconciliation")


@router.get("/chargebacks/export")
async def export_chargebacks(
    request: Request,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(ChargebackCase).where(ChargebackCase.tenant_id == tenant_id)
    if status and status != "all":
        stmt = stmt.where(ChargebackCase.status == status)

    stmt = stmt.order_by(ChargebackCase.created_at.desc()).limit(5000)
    rows = (await session.execute(stmt)).scalars().all()

    out: List[Dict[str, Any]] = []
    for cb in rows:
        out.append(
            {
                "id": cb.id,
                "transaction_id": cb.transaction_id,
                "reason_code": cb.reason_code,
                "status": cb.status,
                "created_at": cb.created_at.isoformat() if cb.created_at else "",
            }
        )

    fieldnames = ["id", "transaction_id", "reason_code", "status", "created_at"]
    return _csv_response(dicts_to_csv_bytes(out, fieldnames=fieldnames), "finance_chargebacks")
