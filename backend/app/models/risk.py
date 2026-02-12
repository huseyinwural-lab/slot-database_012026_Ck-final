from typing import Optional, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Enum
import enum
import uuid

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RiskProfile(SQLModel, table=True):
    __tablename__ = "risk_profiles"

    user_id: uuid.UUID = Field(primary_key=True)
    tenant_id: str = Field(index=True)
    
    # Scoring
    risk_score: int = Field(default=0)
    risk_level: RiskLevel = Field(sa_column=Column(Enum(RiskLevel), default=RiskLevel.LOW))
    
    # State
    flags: Dict = Field(default={}, sa_column=Column(JSON))
    
    # Metadata
    last_event_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
