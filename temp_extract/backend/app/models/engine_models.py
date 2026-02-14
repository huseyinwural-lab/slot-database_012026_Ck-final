from typing import Dict
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
import uuid

# Existing models are assumed to be here. 
# We are adding EngineStandardProfile and extending concepts.

class EngineStandardProfile(SQLModel, table=True):
    """
    Standard Engine Profiles (World Class Standards).
    Seeded: Low Risk, Balanced, High Volatility.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    code: str = Field(index=True, unique=True) # e.g. slot.standard.balanced.v1
    name: str
    description: str
    game_type: str = "SLOT" # SLOT, CRASH, etc.
    
    # The immutable standard configuration
    config: Dict = Field(default={}, sa_column=Column(JSON))
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
