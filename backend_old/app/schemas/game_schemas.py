from pydantic import BaseModel
from typing import Optional, Literal

class GameLaunchRequest(BaseModel):
    game_id: str
    currency: str = "USD"

class GameLaunchResponse(BaseModel):
    url: str
    session_id: str

# Canonical Webhook Schema
class ProviderEvent(BaseModel):
    provider_id: str
    event_type: Literal["BET", "WIN", "REFUND"]
    
    # IDs
    session_id: str # Our session ID
    provider_round_id: str
    provider_event_id: str
    
    # Financials
    amount: float
    currency: str
    
    # Metadata
    game_id: Optional[str] = None
    description: Optional[str] = None
    
    # Security
    signature: str

class ProviderResponse(BaseModel):
    status: str = "OK"
    balance: float
    currency: str
    event_id: str
