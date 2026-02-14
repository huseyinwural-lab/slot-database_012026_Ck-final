from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ConfigPreset(BaseModel):
    id: str  # stable identifier, e.g. "crash_96_medium"
    game_type: str  # should match Game.core_type, e.g. "CRASH", "DICE", "TABLE_POKER", "REEL_LINES"
    config_type: str  # e.g. "crash_math", "dice_math", "poker_rules", "rtp", "paytable" etc.
    name: str
    description: Optional[str] = None
    values: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
