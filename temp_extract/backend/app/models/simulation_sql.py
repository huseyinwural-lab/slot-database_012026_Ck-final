from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import Field, SQLModel


class SimulationRun(SQLModel, table=True):
    __tablename__ = "simulation_run"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)

    name: str
    simulation_type: str = Field(index=True)  # game_math|portfolio|bonus|...
    status: str = Field(default="draft", index=True)  # draft|running|completed|failed

    created_by: str
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
