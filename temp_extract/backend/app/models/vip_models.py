from typing import Optional, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class VipTier(SQLModel, table=True):
    """VIP Levels configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    name: str # Bronze, Silver, Gold
    min_points: float = 0.0
    
    # Benefits
    cashback_percent: float = 0.0 # e.g. 5.0 = 5%
    rakeback_percent: float = 0.0
    
    config: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class PlayerVipStatus(SQLModel, table=True):
    """Current state of a player's loyalty."""
    player_id: str = Field(primary_key=True)
    tenant_id: str = Field(index=True)
    
    current_tier_id: Optional[str] = Field(default=None, index=True)
    
    lifetime_points: float = 0.0
    current_points: float = 0.0 # Redeemable balance
    
    # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
    # Use naive UTC datetime to avoid tz-aware insertion errors.
    last_updated: datetime = Field(default_factory=lambda: datetime.utcnow())

class LoyaltyTransaction(SQLModel, table=True):
    """Ledger for Loyalty Points."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(index=True)
    
    type: str # ACCRUAL, REDEMPTION, ADJUSTMENT, EXPIRY
    amount: float # Positive for accrual, Negative for redemption
    
    source_type: str # WAGER, RAKE, BONUS
    source_ref: Optional[str] = None # Game Round ID
    
    balance_after: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
