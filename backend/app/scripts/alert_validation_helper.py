import asyncio
import httpx
import hmac
import hashlib
import logging
import uuid

# Config
BASE_URL = "http://localhost:8001"
SECRET_KEY = "test_secret"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_validator")

def sign_payload(payload: dict, secret: str = SECRET_KEY) -> str:
    canonical = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
    return hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

async def trigger_signature_failure():
    logger.info("Triggering Signature Failure...")
    payload = {"action": "bet", "userId": "u1", "amount": 10}
    payload["hash"] = sign_payload(payload, "WRONG_KEY")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/api/v1/games/callback/pragmatic", json=payload)
        if resp.status_code == 403:
            logger.info("Signature Failure Triggered Successfully (403).")
        else:
            logger.error(f"Failed to trigger signature failure. Got {resp.status_code}")

async def trigger_duplicate_callback():
    logger.info("Triggering Duplicate Callback...")
    tx_id = str(uuid.uuid4())
    payload = {
        "action": "bet",
        "userId": "u1",
        "gameId": "g1",
        "roundId": "r1",
        "reference": tx_id,
        "amount": 1.0,
        "currency": "USD"
    }
    payload["hash"] = sign_payload(payload)
    
    async with httpx.AsyncClient() as client:
        # First Call
        await client.post(f"{BASE_URL}/api/v1/games/callback/pragmatic", json=payload)
        # Second Call (Duplicate)
        resp = await client.post(f"{BASE_URL}/api/v1/games/callback/pragmatic", json=payload)
        
        if resp.status_code == 200:
            logger.info("Duplicate Callback Processed (Idempotent OK). Check Metrics for increment.")
        else:
            logger.error(f"Duplicate callback failed hard: {resp.status_code}")

async def main():
    await trigger_signature_failure()
    await trigger_duplicate_callback()

if __name__ == "__main__":
    asyncio.run(main())
