from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
import uuid

class PlayerRGProfile(SQLModel, table=True):
    """Responsible Gaming Profile for a Player."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(foreign_key="player.id", index=True, unique=True)
    
    # Limits (None = No limit)
    deposit_limit_daily: Optional[float] = None
    deposit_limit_weekly: Optional[float] = None
    deposit_limit_monthly: Optional[float] = None
    
    loss_limit_daily: Optional[float] = None
    loss_limit_weekly: Optional[float] = None
    
    session_time_limit_minutes: Optional[int] = None
    reality_check_interval_minutes: Optional[int] = 60 # Default 1h
    
    # State
    cool_off_until: Optional[datetime] = None
    self_excluded_until: Optional[datetime] = None # If set, blocked until date. If far future, permanent.
    self_excluded_permanent: bool = False
    
    last_reality_check_ack: Optional[datetime] = None
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlayerKYC(SQLModel, table=True):
    """KYC Status for a Player."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(foreign_key="player.id", index=True, unique=True)
    
    status: str = "NOT_STARTED" # NOT_STARTED | PENDING | VERIFIED | REJECTED
    required_level: str = "L1"
    
    provider_ref: Optional[str] = None # External KYC provider ref
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
