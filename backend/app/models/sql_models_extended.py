from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

# --- GAME CONFIG & ASSET MODELS ---

class GameConfigVersion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    game_id: str = Field(foreign_key="game.id", index=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    version: str
    config_snapshot: Dict = Field(default={}, sa_column=Column(JSON))
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GameAsset(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    game_id: str = Field(foreign_key="game.id", index=True)
    asset_type: str # image, video, sound
    url: str
    metadata_json: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- FINANCE MODELS ---

class ReconciliationReport(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    provider_name: str
    period_start: datetime
    period_end: datetime
    total_records: int = 0
    mismatches: int = 0
    status: str = "pending"
    report_data: Dict = Field(default={}, sa_column=Column(JSON)) # Items, summary
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChargebackCase(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    transaction_id: str = Field(foreign_key="transaction.id", index=True)
    reason_code: str
    status: str = "open"
    evidence_files: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FinanceSettings(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True, unique=True)
    auto_payout_limit: float = 0.0
    provider_configs: Dict = Field(default={}, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
