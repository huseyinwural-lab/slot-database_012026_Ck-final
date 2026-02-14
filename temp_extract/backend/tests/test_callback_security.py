import pytest
import hmac
import hashlib
import time
import json
import uuid
from httpx import AsyncClient

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
CALLBACK_URL = "/integrations/callback"
SECRET = "mock-secret"

def sign_payload(body: dict, timestamp: str, nonce: str) -> str:
    body_bytes = json.dumps(body).encode("utf-8")
    msg = f"{timestamp}.{nonce}.".encode("utf-8") + body_bytes
    return hmac.new(SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

@pytest.mark.asyncio
async def test_callback_security_negative():
    async with AsyncClient(base_url=BASE_URL) as client:
        
        payload = {
            "provider_id": "mock-provider",
            "event_type": "BET",
            "session_id": "fake-session",
            "provider_round_id": "rnd-1",
            "provider_event_id": "evt-1",
            "amount": 10.0,
            "currency": "USD"
        }
        
        # Case 1: Missing Headers
        resp = await client.post(CALLBACK_URL, json=payload)
        assert resp.status_code == 401
        
        # Case 2: Invalid Signature
        ts = str(int(time.time()))
        nonce = uuid.uuid4().hex
        headers = {
            "X-Signature": "invalid-sig",
            "X-Timestamp": ts,
            "X-Nonce": nonce
        }
        resp = await client.post(CALLBACK_URL, json=payload, headers=headers)
        assert resp.status_code == 403
        
        # Case 3: Replay Attack (Same Nonce)
        # First valid request (fails logic but passes security)
        sig = sign_payload(payload, ts, nonce)
        headers["X-Signature"] = sig
        
        # Note: Logic will fail (session not found) but Security should PASS (404)
        # or fail if logic runs. Security Middleware runs before route logic?
        # In our code: `security_check: bool = Depends(verify_signature)`
        # If verify_signature raises 409, it stops.
        
        # First call: Should pass security (return 404/500 logic error is fine)
        resp1 = await client.post(CALLBACK_URL, json=payload, headers=headers)
        assert resp1.status_code != 401 and resp1.status_code != 403
        
        # Second call (Replay): Should be 409
        resp2 = await client.post(CALLBACK_URL, json=payload, headers=headers)
        assert resp2.status_code == 409
        
        print("Negative Security Tests PASS")

if __name__ == "__main__":
    # Self-runner
    import asyncio
    asyncio.run(test_callback_security_negative())
