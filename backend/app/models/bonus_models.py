from typing import Optional, List, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

# --- BONUS MODULE MODELS ---

class BonusCampaign(SQLModel, table=True):
    """Defines a bonus offer (Deposit Match or Free Spins)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    name: str
    type: str # 'deposit_match' | 'free_spins'
    status: str = "draft" # draft | active | paused | archived
    
    # Rules: multiplier, min_dep, max_bonus, wagering_mult, eligible_games, expiry_hours
    config: Dict = Field(default={}, sa_column=Column(JSON))
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class BonusGrant(SQLModel, table=True):
    """An instance of a bonus given to a player."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    campaign_id: str = Field(foreign_key="bonuscampaign.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)
    
    amount_granted: float = 0.0
    initial_balance: float = 0.0 # Snapshot
    
    # Wagering Tracking
    wagering_target: float = 0.0
    wagering_contributed: float = 0.0
    
    status: str = "active" # active | completed | expired | forfeited
    
    # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
    granted_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Abuse Tracking
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
