#!/usr/bin/env python3
import asyncio
import httpx
import uuid
import hashlib
import hmac
import json

SECRET_KEY = "test_secret"

def sign_payload(payload: dict) -> str:
    canonical = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

async def debug_provider_callback():
    """Debug the provider callback to see actual response"""
    
    # Use the backend URL from environment
    backend_url = "https://deal-maker-6.preview.emergentagent.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test with a simple balance request first
        tx_id = str(uuid.uuid4())
        payload = {
            "action": "balance",
            "userId": "test_player_123",
            "gameId": "test_game",
            "roundId": "test_round",
            "reference": tx_id,
            "amount": 0.0,
            "currency": "USD"
        }
        payload["hash"] = sign_payload(payload)
        
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        
        response = await client.post(
            f"{backend_url}/api/v1/games/callback/pragmatic",
            json=payload
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"JSON Response: {json.dumps(json_response, indent=2)}")
            except:
                print("Could not parse JSON response")

if __name__ == "__main__":
    asyncio.run(debug_provider_callback())