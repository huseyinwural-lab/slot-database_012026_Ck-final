from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid

class RiskHistory(SQLModel, table=True):
    __tablename__ = "risk_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True, nullable=False)
    tenant_id: str = Field(index=True, nullable=False)
    
    old_score: int
    new_score: int
    old_level: str
    new_level: str
    
    # Versioning
    risk_engine_version: str = Field(default="v1")
    
    change_reason: str # e.g. "Rule: Rapid Deposit", "Manual: Admin"
    changed_by: Optional[str] = None # Admin ID or "System"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
