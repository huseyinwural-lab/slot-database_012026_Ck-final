from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator


class ReconciliationRunCreate(BaseModel):
    provider: str
    window_start: datetime
    window_end: datetime
    dry_run: bool = False
    idempotency_key: Optional[str] = None

    @field_validator("window_end")
    @classmethod
    def validate_window(cls, v: datetime, info):  # type: ignore[override]
        data = info.data
        window_start: Optional[datetime] = data.get("window_start")
        if window_start and v <= window_start:
            raise ValueError("window_end must be greater than window_start")
        return v


class ReconciliationRunOut(BaseModel):
    id: str
    provider: str
    window_start: datetime
    window_end: datetime
    dry_run: bool
    status: str
    created_at: datetime
    updated_at: datetime
    stats_json: Optional[Dict[str, Any]] = None
    error_json: Optional[Dict[str, Any]] = None


class ReconciliationRunListResponse(BaseModel):
    items: List[ReconciliationRunOut]
    meta: Dict[str, Any]
