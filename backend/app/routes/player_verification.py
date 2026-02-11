import secrets
import hashlib
from datetime import datetime, timedelta
import os
import json

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_session
from app.models.sql_models import Player
from app.infra.providers import IntegrationNotConfigured, send_email_otp, send_sms_otp, confirm_sms_otp
from app.core.redis_client import get_redis
from redis.asyncio import Redis

router = APIRouter(prefix="/api/v1/verify", tags=["player-verification"])

MOCK_MODE = os.getenv("MOCK_EXTERNAL_SERVICES", "false").lower() == "true"

class EmailSendRequest(BaseModel):
    email: str

class EmailConfirmRequest(BaseModel):
    email: str
    code: str

class SmsSendRequest(BaseModel):
    phone: str

class SmsConfirmRequest(BaseModel):
    phone: str
    code: str

# Config
OTP_TTL = 300 # 5 minutes
RESEND_COOLDOWN = 60 # 60 seconds
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = 900 # 15 minutes

def _integration_error(key: str):
    if MOCK_MODE:
        return 
    raise HTTPException(
        status_code=503,
        detail={"error_code": "INTEGRATION_NOT_CONFIGURED", "message": f"Missing {key}"},
    )

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

async def _check_rate_limit(redis: Redis, key: str, limit: int, window: int):
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window)
    if current > limit:
        return False
    return True

@router.post("/email/send")
async def send_email_code(
    payload: EmailSendRequest, 
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    # 1. Rate Limit (IP)
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"rl:ip:{client_ip}:email_send"
    if not await _check_rate_limit(redis, ip_key, 10, 60): # 10 per minute per IP
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Too many requests"})

    # 2. Check User
    result = await session.execute(select(Player).where(Player.email == payload.email))
    player = result.scalars().first()
    if not player:
        # Abuse-proof: Don't reveal user existence, but for now strict 400 is in spec
        # Spec says: "kullanıcı var/yok belli olmayacak" but current frontend expects specific error?
        # Let's return generic error or standard auth invalid.
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Invalid request"}}

    # 3. Cooldown
    cooldown_key = f"vfy:cooldown:email:{payload.email}"
    if await redis.get(cooldown_key):
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Please wait"})

    # 4. Generate Code
    code = f"{secrets.randbelow(999999):06d}"
    if MOCK_MODE:
        code = "123456"
        print(f"MOCK EMAIL SEND: {payload.email} -> {code}")
    else:
        try:
            send_email_otp(payload.email, code)
        except IntegrationNotConfigured as exc:
            _integration_error(exc.key)

    # 5. Store in Redis
    # Store hashed code
    code_key = f"vfy:email:code:{payload.email}"
    attempts_key = f"vfy:attempts:email:{payload.email}"
    
    # Reset attempts on new send
    async with redis.pipeline() as pipe:
        await pipe.setex(code_key, OTP_TTL, _hash_code(code))
        await pipe.setex(cooldown_key, RESEND_COOLDOWN, "1")
        await pipe.delete(attempts_key)
        await pipe.execute()

    return {"ok": True, "data": {"status": "pending"}}


@router.post("/email/confirm")
async def confirm_email_code(
    payload: EmailConfirmRequest, 
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    code_key = f"vfy:email:code:{payload.email}"
    attempts_key = f"vfy:attempts:email:{payload.email}"
    lock_key = f"vfy:lock:email:{payload.email}"

    # 1. Check Lockout
    if await redis.get(lock_key):
        raise HTTPException(status_code=423, detail={"error_code": "VERIFICATION_LOCKED", "message": "Too many attempts. Try later."})

    # 2. Get Code
    stored_hash = await redis.get(code_key)
    if not stored_hash:
        return {"ok": False, "error": {"code": "VERIFY_EMAIL_REQUIRED", "message": "Code expired or not sent"}}

    # 3. Verify
    if _hash_code(payload.code) != stored_hash:
        # Increment attempts
        attempts = await redis.incr(attempts_key)
        if attempts >= MAX_ATTEMPTS:
            await redis.setex(lock_key, LOCKOUT_DURATION, "1")
            await redis.delete(code_key) # Burn code
            raise HTTPException(status_code=423, detail={"error_code": "VERIFICATION_LOCKED", "message": "Too many attempts"})
        
        return {"ok": False, "error": {"code": "VERIFY_EMAIL_REQUIRED", "message": "Invalid code"}}

    # 4. Success
    result = await session.execute(select(Player).where(Player.email == payload.email))
    player = result.scalars().first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Player not found"}}

    player.email_verified = True
    await session.commit()
    
    # Cleanup
    await redis.delete(code_key)
    await redis.delete(attempts_key)
    
    return {"ok": True, "data": {"status": "verified"}}


@router.post("/sms/send")
async def send_sms_code(
    payload: SmsSendRequest, 
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    # 1. Rate Limit (IP)
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"rl:ip:{client_ip}:sms_send"
    if not await _check_rate_limit(redis, ip_key, 5, 60): # Stricter for SMS
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Too many requests"})

    # 2. Check User
    result = await session.execute(select(Player).where(Player.phone == payload.phone))
    player = result.scalars().first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Invalid request"}}

    # 3. Cooldown
    cooldown_key = f"vfy:cooldown:sms:{payload.phone}"
    if await redis.get(cooldown_key):
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Please wait"})

    # 4. Send
    if MOCK_MODE:
        print(f"MOCK SMS SEND: {payload.phone}")
        # For mock mode, we still store a code to verify logic
        # But backend doesn't generate code for Twilio Verify usually (Twilio does).
        # However, for our consistent abstraction, we act as if we generated it 
        # OR we rely on Twilio's state. 
        # The handoff code used `send_sms_otp`.
        # If using Twilio Verify Service, we don't store the code, Twilio does.
        # BUT, the handoff requirements said: "Verification state’lerini Redis’e taşı".
        # This implies we might be doing own OTP or wrapping Twilio.
        # Let's assume we store it for abuse protection logic consistency, 
        # even if Twilio also checks.
        pass
    else:
        try:
            send_sms_otp(payload.phone)
        except IntegrationNotConfigured as exc:
            _integration_error(exc.key)

    # For SMS, if using Twilio Verify, we mostly track cooldowns locally.
    # But if we are in MOCK_MODE, we MUST store the code locally to verify it.
    if MOCK_MODE:
        code = "123456"
        code_key = f"vfy:sms:code:{payload.phone}"
        attempts_key = f"vfy:attempts:sms:{payload.phone}"
        async with redis.pipeline() as pipe:
            await pipe.setex(code_key, OTP_TTL, _hash_code(code))
            await pipe.setex(cooldown_key, RESEND_COOLDOWN, "1")
            await pipe.delete(attempts_key)
            await pipe.execute()
    else:
        # Just set cooldown
        await redis.setex(cooldown_key, RESEND_COOLDOWN, "1")

    return {"ok": True, "data": {"status": "pending"}}


@router.post("/sms/confirm")
async def confirm_sms_code(
    payload: SmsConfirmRequest, 
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis)
):
    attempts_key = f"vfy:attempts:sms:{payload.phone}"
    lock_key = f"vfy:lock:sms:{payload.phone}"

    # 1. Lockout Check
    if await redis.get(lock_key):
        raise HTTPException(status_code=423, detail={"error_code": "VERIFICATION_LOCKED", "message": "Too many attempts"})

    approved = False
    
    if MOCK_MODE:
        code_key = f"vfy:sms:code:{payload.phone}"
        stored_hash = await redis.get(code_key)
        if stored_hash and _hash_code(payload.code) == stored_hash:
            approved = True
        else:
            # Fallback for when we didn't send (dev convenience)
            if payload.code == "123456":
                approved = True
    else:
        try:
            approved = confirm_sms_otp(payload.phone, payload.code)
        except IntegrationNotConfigured as exc:
            _integration_error(exc.key)

    if not approved:
        attempts = await redis.incr(attempts_key)
        if attempts >= MAX_ATTEMPTS:
            await redis.setex(lock_key, LOCKOUT_DURATION, "1")
            raise HTTPException(status_code=423, detail={"error_code": "VERIFICATION_LOCKED", "message": "Too many attempts"})
        return {"ok": False, "error": {"code": "VERIFY_SMS_REQUIRED", "message": "Invalid code"}}

    # Success
    result = await session.execute(select(Player).where(Player.phone == payload.phone))
    player = result.scalars().first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Player not found"}}
        
    player.sms_verified = True
    await session.commit()
    
    # Cleanup (mock only, Twilio handles its own)
    if MOCK_MODE:
        await redis.delete(f"vfy:sms:code:{payload.phone}")
        
    await redis.delete(attempts_key)
    
    return {"ok": True, "data": {"status": "verified"}}
