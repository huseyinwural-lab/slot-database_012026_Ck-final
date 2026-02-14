from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, text, JSON
from sqlmodel import SQLModel, Field
import uuid


class ReconciliationRun(SQLModel, table=True):
    """Reconciliation run metadata and lifecycle state.

    Tracks executions of PSP vs ledger reconciliation jobs.
    """

    __tablename__ = "reconciliation_runs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    provider: str = Field(index=True)

    window_start: datetime = Field()
    window_end: datetime = Field()

    dry_run: bool = Field(default=False)

    status: str = Field(default="queued", index=True)

    idempotency_key: Optional[str] = Field(default=None, index=True)

    stats_json: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    error_json: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
