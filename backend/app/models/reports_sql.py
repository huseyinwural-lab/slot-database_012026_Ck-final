from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import Field, SQLModel


class ReportExportJob(SQLModel, table=True):
    __tablename__ = "report_export_job"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    type: str = Field(index=True)
    status: str = Field(default="completed", index=True)  # processing|completed|failed
    requested_by: str

    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
