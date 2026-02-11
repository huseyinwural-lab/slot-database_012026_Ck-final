from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/verify", tags=["player-verification"])


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
_SMS_CODES = {}


@router.post("/email/send")
async def send_email_code(payload: EmailSendRequest):
    _EMAIL_CODES[payload.email] = "123456"
    return {"ok": True, "data": {"status": "pending"}}


@router.post("/email/confirm")
async def confirm_email_code(payload: EmailConfirmRequest):
    if _EMAIL_CODES.get(payload.email) != payload.code:
        return {"ok": False, "error": {"code": "VERIFY_EMAIL_REQUIRED", "message": "Invalid code"}}
    return {"ok": True, "data": {"status": "verified"}}


@router.post("/sms/send")
async def send_sms_code(payload: SmsSendRequest):
    _SMS_CODES[payload.phone] = "123456"
    return {"ok": True, "data": {"status": "pending"}}


@router.post("/sms/confirm")
async def confirm_sms_code(payload: SmsConfirmRequest):
    if _SMS_CODES.get(payload.phone) != payload.code:
        return {"ok": False, "error": {"code": "VERIFY_SMS_REQUIRED", "message": "Invalid code"}}
    return {"ok": True, "data": {"status": "verified"}}
