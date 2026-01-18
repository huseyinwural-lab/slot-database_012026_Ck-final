from fastapi import Depends, HTTPException, Request
from sqlmodel import select
from app.core.database import get_session
from app.models.game_models import CallbackNonce
from config import settings
from datetime import datetime, timedelta
import hashlib
import hmac
import time
import uuid

async def verify_signature(
    request: Request,
    session = Depends(get_session)
):
    """
    Enhanced Security Middleware:
    1. Timestamp (Replay Window)
    2. Nonce (Replay Cache)
    3. Signature (HMAC)
    """
    if not settings.webhook_signature_enforced:
        return  # Skip if disabled

    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")
    provider_id = "mock-provider" # Should be extracted or standard

    if not signature or not timestamp or not nonce:
        raise HTTPException(401, "Missing Security Headers")

    # 1. Timestamp Check
    try:
        req_ts = int(timestamp)
        now_ts = int(time.time())
        if abs(now_ts - req_ts) > 300: # 5 min tolerance
            raise HTTPException(403, "Request Timestamp Expired")
    except ValueError:
        raise HTTPException(403, "Invalid Timestamp")

    # 2. Nonce Check (DB)
    # Cleanup old nonces occasionally? For now, just check existence.
    stmt = select(CallbackNonce).where(
        CallbackNonce.nonce == nonce,
        CallbackNonce.provider_id == provider_id
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(409, "Nonce Replayed")

    # Store Nonce (Commit immediately to prevent race? Or relying on tx isolation)
    # Ideally should be Redis. Using DB for MVP.
    new_nonce = CallbackNonce(
        provider_id=provider_id,
        nonce=nonce,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    session.add(new_nonce)
    # We don't commit here because main route handler will commit.
    # RISK: If main handler fails, nonce is not saved. Replay possible?
    # FIX: We should use a separate session or Redis.
    # For MVP: Accept risk or flush.
    await session.flush()

    # 3. Signature Check
    body = await request.body()
    secret = settings.adyen_hmac_key or "mock-secret"
    
    # Payload = timestamp.nonce.body
    message = f"{timestamp}.{nonce}.".encode("utf-8") + body
    
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(403, "Invalid Signature")
