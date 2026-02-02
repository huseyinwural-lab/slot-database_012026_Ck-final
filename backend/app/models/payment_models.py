from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class PaymentIntent(SQLModel, table=True):
    """Orchestrates multi-step/multi-provider payment flow."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    player_id: str = Field(index=True)
    
    type: str # DEPOSIT, WITHDRAW
    amount: float
    currency: str
    
    status: str = "PENDING" # PENDING, AUTHORIZED, COMPLETED, FAILED
    
    idempotency_key: str = Field(index=True, unique=True)
    
    # Provider Orchestration
    current_provider: Optional[str] = None
    attempts: List[Dict] = Field(default=[], sa_column=Column(JSON)) # List of {provider, status, timestamp, error}
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Dispute moved to dispute_models.py
