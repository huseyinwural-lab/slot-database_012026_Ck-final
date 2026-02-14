from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import Column
from sqlmodel import Field, SQLModel
from sqlalchemy import JSON


class GameImportJob(SQLModel, table=True):
    __tablename__ = "game_import_job"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    created_by_admin_id: str = Field(index=True)

    status: str = Field(default="queued", index=True)  # queued|running|ready|failed|completed

    source_label: Optional[str] = None
    notes: Optional[str] = None

    client_type: Optional[str] = None
    launch_url: Optional[str] = None
    min_version: Optional[str] = None

    file_name: Optional[str] = None
    file_type: Optional[str] = None  # json|zip
    file_path: Optional[str] = None

    total_items: int = 0
    total_errors: int = 0
    total_imported: int = 0

    error_summary: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GameImportItem(SQLModel, table=True):
    __tablename__ = "game_import_item"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(index=True)
    tenant_id: str = Field(index=True)

    provider_id: Optional[str] = None
    external_id: str = Field(index=True)

    name: Optional[str] = None
    type: Optional[str] = None
    rtp: Optional[float] = None

    status: str = Field(default="pending", index=True)  # pending|valid|invalid|imported|skipped
    errors: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
