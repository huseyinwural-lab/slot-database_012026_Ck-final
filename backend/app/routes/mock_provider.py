from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import uuid
import hashlib
import hmac
import time
import json
from config import settings

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
    Simulate a Game Spin with Security Headers.
    """
    
    CALLBACK_URL = "http://localhost:8001/api/v1/integrations/callback" 
    SECRET = settings.adyen_hmac_key or "mock-secret"
    
    round_id = f"rnd-{uuid.uuid4().hex[:8]}"
    
    async with httpx.AsyncClient() as client:
        
        # Helper to send signed request
        async def send_signed(payload):
            timestamp = str(int(time.time()))
            nonce = uuid.uuid4().hex
            
            body_bytes = json.dumps(payload).encode("utf-8")
            
            # Sign: timestamp.nonce.body
            msg = f"{timestamp}.{nonce}.".encode("utf-8") + body_bytes
            sig = hmac.new(SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()
            
            headers = {
                "X-Signature": sig,
                "X-Timestamp": timestamp,
                "X-Nonce": nonce,
                "X-Provider": "mock-provider"
            }
            
            return await client.post(CALLBACK_URL, content=body_bytes, headers=headers)

        # 1. BET
        bet_payload = {
            "provider_id": "mock-provider",
            "event_type": "BET",
            "session_id": request.session_id,
            "provider_round_id": round_id,
            "provider_event_id": f"evt-{uuid.uuid4().hex}",
            "amount": request.amount,
            "currency": request.currency
        }
        
        resp = await send_signed(bet_payload)
        
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
                "currency": request.currency
            }
            
            resp_win = await send_signed(win_payload)
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
