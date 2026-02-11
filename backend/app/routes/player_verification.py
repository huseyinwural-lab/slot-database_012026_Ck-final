import secrets
from datetime import datetime, timedelta
import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel

from app.core.database import get_session
from app.models.sql_models import Player
from app.infra.providers import IntegrationNotConfigured, send_email_otp, send_sms_otp, confirm_sms_otp

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

_EMAIL_CODES = {}
_SMS_SEND_LOG = {}
_SMS_ATTEMPTS = {}

OTP_TTL = timedelta(minutes=5)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_SMS_ATTEMPTS = 5
SMS_LOCKOUT = timedelta(minutes=15)

def _integration_error(key: str):
    if MOCK_MODE:
        return # Do not raise
    raise HTTPException(
        status_code=503,
        detail={"error_code": "INTEGRATION_NOT_CONFIGURED", "message": f"Missing {key}"},
    )

@router.post("/email/send")
async def send_email_code(payload: EmailSendRequest, session: AsyncSession = Depends(get_session)):
    player = await session.exec(select(Player).where(Player.email == payload.email))
    player = player.first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Player not found"}}

    record = _EMAIL_CODES.get(payload.email)
    now = datetime.utcnow()
    # Mock mode skips rate limit for ease of testing if needed, or keep it. Keeping it.
    if record and now - record["sent_at"] < RESEND_COOLDOWN:
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Please wait"})

    code = f"{secrets.randbelow(999999):06d}"
    if MOCK_MODE:
        # Fixed code for mock
        code = "123456"
        print(f"MOCK EMAIL SEND: {payload.email} -> {code}")
    else:
        try:
            send_email_otp(payload.email, code)
        except IntegrationNotConfigured as exc:
            _integration_error(exc.key)

    _EMAIL_CODES[payload.email] = {
        "code": code,
        "expires_at": now + OTP_TTL,
        "sent_at": now,
    }
    return {"ok": True, "data": {"status": "pending"}}


@router.post("/email/confirm")
async def confirm_email_code(payload: EmailConfirmRequest, session: AsyncSession = Depends(get_session)):
    record = _EMAIL_CODES.get(payload.email)
    if not record:
        # In mock mode, allow if code is 123456 even if not "sent" explicitly? 
        # Better to require send first to test flow.
        return {"ok": False, "error": {"code": "VERIFY_EMAIL_REQUIRED", "message": "Code not sent"}}
    
    if datetime.utcnow() > record["expires_at"]:
        return {"ok": False, "error": {"code": "VERIFY_EMAIL_REQUIRED", "message": "Code expired"}}
    
    if record["code"] != payload.code:
        return {"ok": False, "error": {"code": "VERIFY_EMAIL_REQUIRED", "message": "Invalid code"}}

    player = await session.exec(select(Player).where(Player.email == payload.email))
    player = player.first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Player not found"}}

    player.email_verified = True
    await session.commit()
    return {"ok": True, "data": {"status": "verified"}}


@router.post("/sms/send")
async def send_sms_code(payload: SmsSendRequest, session: AsyncSession = Depends(get_session)):
    player = await session.exec(select(Player).where(Player.phone == payload.phone))
    player = player.first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Player not found"}}

    now = datetime.utcnow()
    last_sent = _SMS_SEND_LOG.get(payload.phone)
    if last_sent and now - last_sent < RESEND_COOLDOWN:
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Please wait"})

    if MOCK_MODE:
        print(f"MOCK SMS SEND: {payload.phone}")
    else:
        try:
            send_sms_otp(payload.phone)
        except IntegrationNotConfigured as exc:
            _integration_error(exc.key)

    _SMS_SEND_LOG[payload.phone] = now
    _SMS_ATTEMPTS[payload.phone] = {"count": 0, "first": now}
    return {"ok": True, "data": {"status": "pending"}}


@router.post("/sms/confirm")
async def confirm_sms_code(payload: SmsConfirmRequest, session: AsyncSession = Depends(get_session)):
    attempt = _SMS_ATTEMPTS.get(payload.phone, {"count": 0, "first": datetime.utcnow()})
    if attempt["count"] >= MAX_SMS_ATTEMPTS and datetime.utcnow() - attempt["first"] < SMS_LOCKOUT:
        raise HTTPException(status_code=429, detail={"error_code": "RATE_LIMIT", "message": "Too many attempts"})

    approved = False
    if MOCK_MODE:
        if payload.code == "123456":
            approved = True
    else:
        try:
            approved = confirm_sms_otp(payload.phone, payload.code)
        except IntegrationNotConfigured as exc:
            _integration_error(exc.key)

    if not approved:
        attempt["count"] += 1
        _SMS_ATTEMPTS[payload.phone] = attempt
        return {"ok": False, "error": {"code": "VERIFY_SMS_REQUIRED", "message": "Invalid code"}}

    player = await session.exec(select(Player).where(Player.phone == payload.phone))
    player = player.first()
    if not player:
        return {"ok": False, "error": {"code": "AUTH_INVALID", "message": "Player not found"}}
    player.sms_verified = True
    await session.commit()
    return {"ok": True, "data": {"status": "verified"}}
