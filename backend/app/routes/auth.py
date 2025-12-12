from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.models.domain.admin import AdminUser
from app.models.domain.admin import AdminStatus
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_admin_by_email,
    get_current_admin,
)
from config import settings
from app.routes.admin import get_db


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminUser


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class AcceptInviteRequest(BaseModel):
    token: str
    new_password: str


def _validate_password_policy(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PASSWORD_TOO_SHORT",
        )
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PASSWORD_MUST_CONTAIN_UPPERCASE",
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PASSWORD_MUST_CONTAIN_DIGIT",
        )
    if not any(not c.isalnum() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PASSWORD_MUST_CONTAIN_SPECIAL",
        )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: LoginRequest = Body(...)):
    db = get_db()
    admin = await get_admin_by_email(form_data.email)
    if not admin or not admin.is_active or not admin.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    if not verify_password(form_data.password, admin.password_hash):
        await db.admins.update_one(
            {"id": admin.id},
            {"$inc": {"failed_login_attempts": 1}},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    # Reset failed attempts and update last_login
    await db.admins.update_one(
        {"id": admin.id},
        {
            "$set": {
                "failed_login_attempts": 0,
                "last_login": datetime.now(timezone.utc),
            }
        },
    )

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    access_token = create_access_token(
        data={"sub": admin.id, "email": admin.email},
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=access_token, admin=admin)


@router.get("/me", response_model=AdminUser)
async def get_me(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin


@router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, current_admin: AdminUser = Depends(get_current_admin)):
    db = get_db()

    if not current_admin.password_hash:
        raise HTTPException(status_code=400, detail="PASSWORD_NOT_SET")

    if not verify_password(payload.current_password, current_admin.password_hash):
        raise HTTPException(status_code=400, detail="CURRENT_PASSWORD_INVALID")

    _validate_password_policy(payload.new_password)

    password_hash = get_password_hash(payload.new_password)
    await db.admins.update_one(
        {"id": current_admin.id},
        {
            "$set": {
                "password_hash": password_hash,
                "last_password_change_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": "PASSWORD_CHANGED"}


@router.post("/request-password-reset")
async def request_password_reset(payload: PasswordResetRequest):
    db = get_db()
    admin = await get_admin_by_email(payload.email)

    # E-posta sızdırmamak için her durumda aynı cevabı döndür.
    if not admin:
        return {"message": "RESET_REQUEST_ACCEPTED"}

    token = create_access_token(
        data={"sub": admin.id, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=30),
    )

    await db.admins.update_one(
        {"id": admin.id},
        {
            "$set": {
                "password_reset_token": token,
                "password_reset_expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
            }
        },
    )

    # V1: Mail entegrasyonu yok, sadece token
    # Gerçek dünyada burada e-posta gönderilir.
    return {"message": "RESET_REQUEST_ACCEPTED", "reset_token": token}


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirmRequest):
    db = get_db()

    from jose import jwt, JWTError

    try:
        data = jwt.decode(
            payload.token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise HTTPException(status_code=400, detail="RESET_TOKEN_INVALID")

    if data.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="RESET_TOKEN_INVALID")

    admin_id = data.get("sub")
    if not admin_id:
        raise HTTPException(status_code=400, detail="RESET_TOKEN_INVALID")

    admin_doc = await db.admins.find_one({"id": admin_id}, {"_id": 0})
    if not admin_doc:
        raise HTTPException(status_code=400, detail="RESET_TOKEN_INVALID")

    stored_token = admin_doc.get("password_reset_token")
    expires_at = admin_doc.get("password_reset_expires_at")

    if not stored_token or stored_token != payload.token:
        raise HTTPException(status_code=400, detail="RESET_TOKEN_INVALID")

    if expires_at:
        if isinstance(expires_at, str):
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        else:
            # Handle datetime object from MongoDB
            if expires_at.tzinfo is None:
                expires_dt = expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_dt = expires_at
        if expires_dt < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="RESET_TOKEN_EXPIRED")

    _validate_password_policy(payload.new_password)

    password_hash = get_password_hash(payload.new_password)
    await db.admins.update_one(
        {"id": admin_id},
        {
            "$set": {
                "password_hash": password_hash,
                "last_password_change_at": datetime.now(timezone.utc),
            },
            "$unset": {
                "password_reset_token": "",
                "password_reset_expires_at": "",
            },
        },
    )

    return {"message": "PASSWORD_RESET_SUCCESS"}


@router.post("/accept-invite")
async def accept_invite(payload: AcceptInviteRequest):
    db = get_db()

    from jose import jwt, JWTError

    try:
        data = jwt.decode(
            payload.token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise HTTPException(status_code=400, detail="INVITE_TOKEN_INVALID")

    if data.get("purpose") != "invite":
        raise HTTPException(status_code=400, detail="INVITE_TOKEN_INVALID")

    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="INVITE_TOKEN_INVALID")

    admin_doc = await db.admins.find_one({"email": email}, {"_id": 0})
    if not admin_doc:
        raise HTTPException(status_code=400, detail="INVITE_TOKEN_INVALID")

    # Only invited admins can accept an invite
    if admin_doc.get("status") != AdminStatus.INVITED:
        raise HTTPException(status_code=400, detail="INVITE_NOT_PENDING")

    invite_token = admin_doc.get("invite_token")
    invite_expires_at = admin_doc.get("invite_expires_at")

    if not invite_token or invite_token != payload.token:
        raise HTTPException(status_code=400, detail="INVITE_TOKEN_INVALID")

    # Optional: server-side expiry check (in addition to JWT exp)
    if invite_expires_at:
        if isinstance(invite_expires_at, str):
            expires_dt = datetime.fromisoformat(invite_expires_at.replace('Z', '+00:00'))
        else:
            if invite_expires_at.tzinfo is None:
                expires_dt = invite_expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_dt = invite_expires_at
        if expires_dt < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="INVITE_TOKEN_EXPIRED")

    _validate_password_policy(payload.new_password)

    password_hash = get_password_hash(payload.new_password)
    await db.admins.update_one(
        {"email": email},
        {
            "$set": {
                "password_hash": password_hash,
                "status": AdminStatus.ACTIVE,
                "last_password_change_at": datetime.now(timezone.utc),
            },
            "$unset": {
                "invite_token": "",
                "invite_expires_at": "",
            },
        },
    )

    return {"message": "INVITE_ACCEPTED"}
