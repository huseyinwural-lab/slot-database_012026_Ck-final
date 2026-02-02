from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class GameImportJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: Optional[str] = None
    source: str = "manual"  # "provider" | "manual"
    status: str = "created"  # "created", "fetching", "fetched", "importing", "completed", "failed"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str
    completed_at: Optional[datetime] = None
    total_found: int = 0
    total_imported: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    logs: List[Dict[str, Any]] = []


class GameImportItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    provider: Optional[str] = None
    provider_game_id: str
    name: str
    category: str  # "slot", "live", "table", "crash", "dice"
    rtp: Optional[float] = None
    status: str = "pending"  # "pending", "ready", "imported", "error", "skipped"
    errors: List[str] = []
    warnings: List[str] = []
    already_exists: bool = False
    raw_payload: Optional[Dict[str, Any]] = None
    # Client runtime metadata (optional for backwards compatibility)
    client_type: Optional[str] = None  # "html5" | "unity"
    client_launch_url: Optional[str] = None
    client_min_version: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
