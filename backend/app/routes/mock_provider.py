from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import uuid
import hashlib
from typing import Literal

router = APIRouter(prefix="/api/v1/mock-provider", tags=["mock_provider"])

class MockSpinRequest(BaseModel):
    session_id: str
    amount: float
    is_win: bool = False
    win_amount: float = 0.0
    currency: str = "USD"

@router.post("/spin")
async def mock_spin(request: MockSpinRequest):
    """
    Simulate a Game Spin.
    1. Sends BET webhook to Backend.
    2. If is_win, sends WIN webhook to Backend.
    """
    
    CALLBACK_URL = "http://localhost:8001/api/v1/integrations/callback" # Internal ref
    
    round_id = f"rnd-{uuid.uuid4().hex[:8]}"
    
    # 1. BET
    bet_payload = {
        "provider_id": "mock-provider",
        "event_type": "BET",
        "session_id": request.session_id,
        "provider_round_id": round_id,
        "provider_event_id": f"evt-{uuid.uuid4().hex}",
        "amount": request.amount,
        "currency": request.currency,
        "signature": "mock-sig"
    }
    
    async with httpx.AsyncClient() as client:
        # Call Backend
        resp = await client.post(CALLBACK_URL, json=bet_payload, timeout=5.0)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Bet Failed: {resp.text}")
            
        bet_data = resp.json()
        
        # 2. WIN (Optional)
        if request.is_win:
            win_payload = {
                "provider_id": "mock-provider",
                "event_type": "WIN",
                "session_id": request.session_id,
                "provider_round_id": round_id,
                "provider_event_id": f"evt-{uuid.uuid4().hex}",
                "amount": request.win_amount,
                "currency": request.currency,
                "signature": "mock-sig"
            }
            
            resp_win = await client.post(CALLBACK_URL, json=win_payload, timeout=5.0)
            if resp_win.status_code != 200:
                 raise HTTPException(status_code=resp_win.status_code, detail=f"Win Failed: {resp_win.text}")
            
            return {
                "status": "success", 
                "round_id": round_id, 
                "bet_balance": bet_data["balance"],
                "final_balance": resp_win.json()["balance"],
                "win": request.win_amount
            }
            
        return {
            "status": "success", 
            "round_id": round_id, 
            "final_balance": bet_data["balance"],
            "win": 0.0
        }
