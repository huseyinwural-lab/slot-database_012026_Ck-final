from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.sql_models import AdminUser
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_admin_by_email,
    get_current_admin,
)
from config import settings
from app.core.database import get_session
from app.core.errors import AppError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

from app.schemas.token import TokenResponse

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
        raise AppError(error_code="PASSWORD_TOO_SHORT", message="Password must be at least 8 characters long", status_code=400)
    if not any(c.isupper() for c in password):
        raise AppError(error_code="PASSWORD_MUST_CONTAIN_UPPERCASE", message="Password must contain at least one uppercase letter", status_code=400)
    if not any(c.isdigit() for c in password):
        raise AppError(error_code="PASSWORD_MUST_CONTAIN_DIGIT", message="Password must contain at least one digit", status_code=400)
    if not any(not c.isalnum() for c in password):
        raise AppError(error_code="PASSWORD_MUST_CONTAIN_SPECIAL", message="Password must contain at least one special character", status_code=400)

@router.post("/login", response_model=TokenResponse)
async def login(form_data: LoginRequest = Body(...), session: AsyncSession = Depends(get_session)):
    # 1. Fetch User
    statement = select(AdminUser).where(AdminUser.email == form_data.email)
    result = await session.execute(statement) # Changed exec to execute
    admin = result.scalars().first()

    auth_error = AppError(error_code="INVALID_CREDENTIALS", message="Invalid email or password", status_code=401)

    if not admin or not admin.is_active or not admin.password_hash:
        raise auth_error

    # 2. Verify Password
    if not verify_password(form_data.password, admin.password_hash):
        admin.failed_login_attempts += 1
        await session.commit()
        raise auth_error

    # 3. Success Update
    admin.failed_login_attempts = 0
    await session.commit()
    await session.refresh(admin)

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    access_token = create_access_token(
        data={"sub": admin.id, "email": admin.email, "tenant_id": admin.tenant_id, "role": admin.role},
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=access_token, admin_email=admin.email, admin_role=admin.role)

from app.schemas.admin import AdminUserPublic


@router.get("/me", response_model=AdminUserPublic)
async def get_me(current_admin: AdminUser = Depends(get_current_admin)):
    return AdminUserPublic.model_validate(current_admin)

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest, 
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    if not current_admin.password_hash:
        raise AppError(error_code="PASSWORD_NOT_SET", message="Password is not set", status_code=400)

    if not verify_password(payload.current_password, current_admin.password_hash):
        raise AppError(error_code="CURRENT_PASSWORD_INVALID", message="Incorrect password", status_code=400)

    _validate_password_policy(payload.new_password)

    current_admin.password_hash = get_password_hash(payload.new_password)
    session.add(current_admin)
    await session.commit()
    
    return {"message": "PASSWORD_CHANGED"}

@router.post("/request-password-reset")
async def request_password_reset(payload: PasswordResetRequest, session: AsyncSession = Depends(get_session)):
    statement = select(AdminUser).where(AdminUser.email == payload.email)
    result = await session.execute(statement) # Changed exec to execute
    admin = result.scalars().first()

    if not admin:
        return {"message": "RESET_REQUEST_ACCEPTED"}

    token = create_access_token(
        data={"sub": admin.id, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=30),
    )

    admin.password_reset_token = token
    session.add(admin)
    await session.commit()

    return {"message": "RESET_REQUEST_ACCEPTED", "reset_token": token}

@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirmRequest, session: AsyncSession = Depends(get_session)):
    from jose import jwt, JWTError
    
    try:
        data = jwt.decode(payload.token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise AppError(error_code="RESET_TOKEN_INVALID", message="Invalid token", status_code=400)

    if data.get("purpose") != "password_reset":
        raise AppError(error_code="RESET_TOKEN_INVALID", message="Invalid purpose", status_code=400)

    admin_id = data.get("sub")
    statement = select(AdminUser).where(AdminUser.id == admin_id)
    result = await session.execute(statement) # Changed exec to execute
    admin = result.scalars().first()

    if not admin or admin.password_reset_token != payload.token:
        raise AppError(error_code="RESET_TOKEN_INVALID", message="Token mismatch or user not found", status_code=400)

    _validate_password_policy(payload.new_password)
    admin.password_hash = get_password_hash(payload.new_password)
    admin.password_reset_token = None
    session.add(admin)
    await session.commit()

    return {"message": "PASSWORD_RESET_SUCCESS"}

@router.post("/accept-invite")
async def accept_invite(payload: AcceptInviteRequest, session: AsyncSession = Depends(get_session)):
    from jose import jwt, JWTError
    try:
        data = jwt.decode(payload.token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise AppError(error_code="INVITE_TOKEN_INVALID", message="Invalid token", status_code=400)

    if data.get("purpose") != "invite":
        raise AppError(error_code="INVITE_TOKEN_INVALID", message="Invalid purpose", status_code=400)

    email = data.get("email")
    statement = select(AdminUser).where(AdminUser.email == email)
    result = await session.execute(statement) # Changed exec to execute
    admin = result.scalars().first()

    if not admin:
        raise AppError(error_code="INVITE_TOKEN_INVALID", message="User not found", status_code=400)

    # In SQL Model, verify invite_token matches
    if admin.invite_token != payload.token:
        raise AppError(error_code="INVITE_TOKEN_INVALID", message="Token mismatch", status_code=400)

    _validate_password_policy(payload.new_password)
    admin.password_hash = get_password_hash(payload.new_password)
    admin.invite_token = None
    admin.status = "active"
    
    session.add(admin)
    await session.commit()

    return {"message": "INVITE_ACCEPTED"}
