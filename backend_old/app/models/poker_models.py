from typing import Optional, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class RakeProfile(SQLModel, table=True):
    """Configuration for Rake calculation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    name: str = Field(index=True) # e.g. "Standard Cash No Limit"
    game_type: str = "CASH" # CASH | TOURNAMENT
    
    percentage: float = 5.0 # e.g. 5%
    cap: float = 3.0 # Max rake per hand
    
    # Advanced rules can be JSON: { "3-4_players": {cap: 2.0}, "heads_up": {cap: 1.0} }
    rules: Dict = Field(default={}, sa_column=Column(JSON))
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PokerHandAudit(SQLModel, table=True):
    """Audit record for a finished poker hand."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    provider_hand_id: str = Field(index=True)
    table_id: str
    game_type: str
    
    pot_total: float
    rake_collected: float
    rake_profile_id: Optional[str] = Field(foreign_key="rakeprofile.id")
    
    # List of winners and amounts: [{"player_id": "...", "win": 50.0}]
    winners: Dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
