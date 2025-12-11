from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime, timezone
import uuid


class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = "renter"  # "owner" | "renter"
    features: Dict[str, bool] = {
        "can_use_game_robot": True,
        "can_edit_configs": True,
        "can_manage_bonus": True,
        "can_view_reports": True,
    }
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
