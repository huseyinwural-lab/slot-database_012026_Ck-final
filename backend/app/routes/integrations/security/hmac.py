from fastapi import Depends, HTTPException, Request
from config import settings
import hmac
import hashlib
import time
from typing import Optional

def verify_hmac_signature(request: Request, secret: str, header_prefix: str = "X"):
    """
    Generic HMAC signature verification.
    """
    if not settings.webhook_signature_enforced:
        return True
        
    signature = request.headers.get(f"{header_prefix}-Signature")
    timestamp = request.headers.get(f"{header_prefix}-Timestamp")
    
    if not signature or not timestamp:
        raise HTTPException(401, "Missing signature headers")
        
    # Replay protection (5 mins)
    now = int(time.time())
    try:
        ts_int = int(timestamp)
    except ValueError:
        raise HTTPException(401, "Invalid timestamp format")

    if abs(now - ts_int) > 300:
        raise HTTPException(401, "Timestamp expired")
        
    return True # In a real implementation we would await body and hash it, but this is a dependency function stub for now

class SecurityContext:
    @staticmethod
    async def verify_poker(request: Request):
        return verify_hmac_signature(request, settings.audit_export_secret) # Placeholder secret
