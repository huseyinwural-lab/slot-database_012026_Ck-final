from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

class Dispute(SQLModel, table=True):
    """Payment Dispute / Chargeback Case."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    # Link to original transaction
    transaction_id: str = Field(index=True) 
    # Not using Foreign Key constraint strictly to allow archiving transactions differently, 
    # but logically it links to Transaction.id
    
    player_id: str = Field(index=True)
    amount: float
    currency: str = "USD"
    
    reason_code: Optional[str] = None # e.g. "fraudulent", "unrecognized"
    status: str = Field(default="OPEN", index=True) # OPEN, UNDER_REVIEW, WON, LOST
    
    evidence_files: List[str] = Field(default=[], sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None

class AffiliateClawback(SQLModel, table=True):
    """Record of commission reversal due to chargeback."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    
    affiliate_id: str = Field(index=True)
    original_commission_id: Optional[str] = None # Link to LedgerTransaction of type 'affiliate_commission'
    
    dispute_id: str = Field(foreign_key="dispute.id")
    amount_reversed: float
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
