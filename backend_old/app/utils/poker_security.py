from fastapi import HTTPException, Request
from config import settings
import hmac
import hashlib
import time

async def verify_poker_callback_signature(request: Request):
    """
    Verify HMAC signature for Poker Provider callbacks.
    Headers: X-Signature, X-Timestamp
    """
    if not settings.webhook_signature_enforced:
        return True
        
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    
    if not signature or not timestamp:
        raise HTTPException(401, "Missing signature headers")
        
    # Replay protection (5 mins)
    now = int(time.time())
    if abs(now - int(timestamp)) > 300:
        raise HTTPException(401, "Timestamp expired")
        
    body = await request.body()
    payload = body.decode()
    
    # HMAC-SHA256(timestamp + body, secret)
    message = f"{timestamp}{payload}"
    expected_sig = hmac.new(
        settings.audit_export_secret.encode(), # Using audit secret as placeholder for provider secret
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(401, "Invalid signature")
        
    return True
