from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class PaymentAttempt(SQLModel, table=True):
    """Granular tracking of each payment provider interaction."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    payment_intent_id: str = Field(foreign_key="paymentintent.id", index=True)
    
    provider: str = Field(index=True)
    attempt_no: int
    
    status: str # SUCCESS, FAILED, DECLINED
    raw_code: Optional[str] = None
    retryable: bool = False
    
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RoutingRule(SQLModel, table=True):
    """Smart Routing V2 Rules."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: Optional[str] = Field(default=None, index=True) # Global if None
    
    country: Optional[str] = None
    currency: Optional[str] = None
    method: Optional[str] = None
    bin_prefix: Optional[str] = None
    
    provider_priority: List[str] = Field(sa_column=Column(JSON)) # ["stripe", "adyen"]
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
