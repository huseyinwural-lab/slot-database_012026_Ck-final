from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict

from sqlmodel import SQLModel, Field, Column, JSON
import uuid


class ReconciliationFinding(SQLModel, table=True):
    """Persistent storage for PSP vs. ledger reconciliation findings."""

    __tablename__ = "reconciliation_findings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    provider: str = Field(index=True)

    tenant_id: Optional[str] = Field(default=None, index=True)
    player_id: Optional[str] = Field(default=None, index=True)
    tx_id: Optional[str] = Field(default=None, index=True)

    provider_event_id: Optional[str] = Field(default=None, index=True)
    provider_ref: Optional[str] = Field(default=None, index=True)

    finding_type: str = Field(index=True)  # e.g. missing_in_ledger, missing_in_psp, amount_mismatch
    severity: str = Field(default="INFO", index=True)  # INFO, WARN, ERROR
    status: str = Field(default="OPEN", index=True)  # OPEN, RESOLVED

    message: Optional[str] = None
    raw: Dict = Field(default_factory=dict, sa_column=Column(JSON))


async def create_finding(session, **kwargs) -> ReconciliationFinding:
    """Idempotent create helper for reconciliation findings.

    Uniqueness key (MVP): (provider, provider_event_id, finding_type).
    If a finding with the same triple already exists, it is returned instead
    of inserting a new row.
    """

    from sqlmodel import select
    from sqlalchemy.exc import IntegrityError

    provider = kwargs.get("provider")
    provider_event_id = kwargs.get("provider_event_id")
    finding_type = kwargs.get("finding_type")

    stmt = None
    if provider and provider_event_id and finding_type:
        stmt = select(ReconciliationFinding).where(
            ReconciliationFinding.provider == provider,
            ReconciliationFinding.provider_event_id == provider_event_id,
            ReconciliationFinding.finding_type == finding_type,
        )
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return existing

    finding = ReconciliationFinding(**kwargs)
    session.add(finding)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if stmt is not None:
            res = await session.execute(stmt)
            existing = res.scalars().first()
            if existing:
                return existing
        raise

    await session.refresh(finding)
    return finding


async def list_findings(session, **filters):
    from sqlmodel import select

    stmt = select(ReconciliationFinding)
    if provider := filters.get("provider"):
        stmt = stmt.where(ReconciliationFinding.provider == provider)
    if status := filters.get("status"):
        stmt = stmt.where(ReconciliationFinding.status == status)
    if tenant_id := filters.get("tenant_id"):
        stmt = stmt.where(ReconciliationFinding.tenant_id == tenant_id)

    result = await session.execute(stmt)
    return result.scalars().all()


async def resolve_finding(session, finding_id: str) -> Optional[ReconciliationFinding]:
    finding = await session.get(ReconciliationFinding, finding_id)
    if not finding:
        return None
    finding.status = "RESOLVED"
    finding.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(finding)
    return finding
