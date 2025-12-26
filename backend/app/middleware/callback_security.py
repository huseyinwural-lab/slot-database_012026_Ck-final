from fastapi import Depends, HTTPException, Request
from config import settings
import hashlib
import hmac
import time

async def verify_signature(request: Request):
    """
    Middleware/Dependency to verify Provider Webhook Signature.
    Expects X-Signature (HMAC-SHA256) and X-Timestamp.
    """
    if not settings.webhook_signature_enforced:
        return # Skip in dev/mock if configured

    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    
    if not signature or not timestamp:
        raise HTTPException(401, "Missing Security Headers")
        
    # 1. Timestamp Check (Replay Protection - 5 min tolerance)
    try:
        req_ts = int(timestamp)
        now_ts = int(time.time())
        if abs(now_ts - req_ts) > 300:
            raise HTTPException(401, "Request Timestamp Expired")
    except ValueError:
        raise HTTPException(401, "Invalid Timestamp")

    # 2. Signature Check
    body = await request.body()
    secret = settings.adyen_hmac_key or "mock-secret" # Use provider specific secret
    
    # Construct payload: timestamp.body
    message = f"{timestamp}.".encode("utf-8") + body
    
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(401, "Invalid Signature")
