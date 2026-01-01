from typing import Optional, List, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
import uuid

class Affiliate(SQLModel, table=True):
    """Affiliate Partner."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str
    email: str
    
    # Commission Plan
    commission_type: str = "CPA" # CPA, REVSHARE, HYBRID
    cpa_amount: float = 0.0
    cpa_threshold: float = 20.0
    revshare_percent: float = 0.0
    commission_rate: float = 0.0 # Legacy field for DB compatibility
    
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AffiliateLink(SQLModel, table=True):
    """Tracking Links."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    affiliate_id: str = Field(foreign_key="affiliate.id", index=True)
    tenant_id: str = Field(index=True)
    
    code: str = Field(index=True, unique=True) # e.g. "SUMMER25"
    campaign: str = "default"
    
    clicks: int = 0
    signups: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AffiliateAttribution(SQLModel, table=True):
    """Player -> Affiliate Mapping."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    player_id: str = Field(index=True, unique=True) # 1:1 attribution
    affiliate_id: str = Field(foreign_key="affiliate.id", index=True)
    link_id: Optional[str] = None
    
    attribution_type: str = "last_click"
    # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
    attributed_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    # Status
    status: str = "active" # active, revoked (fraud)

class GrowthEvent(SQLModel, table=True):
    """Event Stream for CRM/Affiliate triggers."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    event_type: str # USER_SIGNUP, FIRST_DEPOSIT, CHURN_RISK
    player_id: str = Field(index=True)
    
    payload: Dict = Field(default={}, sa_column=Column(JSON))
    
    processed: bool = False
    # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
    # Use naive UTC datetime to avoid tz-aware insertion errors.
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
