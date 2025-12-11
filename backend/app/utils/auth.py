from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config import settings
from app.models.domain.admin import AdminUser, AdminAPIKey
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.api_keys import get_admin_api_key


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TOKEN_CREATION_FAILED",
        ) from exc
    return encoded_jwt


async def get_admin_by_id(admin_id: str) -> Optional[AdminUser]:
    db = get_db()
    doc = await db.admins.find_one({"id": admin_id}, {"_id": 0})
    return AdminUser(**doc) if doc else None


async def get_admin_by_email(email: str) -> Optional[AdminUser]:
    db = get_db()
    doc = await db.admins.find_one({"email": email}, {"_id": 0})
    return AdminUser(**doc) if doc else None


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = await get_admin_by_id(admin_id)
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin


def require_permission(permission: str):
    async def dependency(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        # Simple permission model: Super Admin ("*" in role perms) bypasses checks.
        db = get_db()
        role_doc = await db.admin_roles.find_one({"name": current_admin.role}, {"_id": 0})
        if not role_doc:
            raise HTTPException(status_code=403, detail="ROLE_NOT_FOUND")

        permissions = role_doc.get("permissions", [])
        if "*" in permissions or permission in permissions:
            return current_admin

        raise HTTPException(status_code=403, detail="PERMISSION_DENIED")


class AdminAPIKeyContext(BaseModel):
    api_key: AdminAPIKey
    tenant_id: str
    scopes: list[str]


async def get_api_key_context(authorization: str = Header(None)) -> AdminAPIKeyContext:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "API_KEY_MISSING", "message": "Authorization Bearer api-key required"},
        )

    raw_key = authorization.split(" ", 1)[1].strip()
    db = get_db()
    api_key = await get_admin_api_key(db, raw_key)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "API_KEY_INVALID"},
        )

    return AdminAPIKeyContext(api_key=api_key, tenant_id=api_key.tenant_id, scopes=api_key.scopes)


def require_scope(context: AdminAPIKeyContext, scope: str) -> None:
    if scope not in context.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "API_KEY_SCOPE_FORBIDDEN", "scope": scope},
        )
