from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.sql_models import AdminUser, APIKey
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_password(plain_password, hashed_password):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta):
    from datetime import datetime, timezone
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    statement = select(AdminUser).where(AdminUser.email == email)
    result = await session.execute(statement)
    admin = result.scalars().first()
    
    if admin is None:
        raise credentials_exception
    return admin

async def get_admin_by_email(email: str, session: AsyncSession) -> AdminUser | None:
    statement = select(AdminUser).where(AdminUser.email == email)
    result = await session.execute(statement)
    return result.scalars().first()

from pydantic import BaseModel
from typing import List

class AdminAPIKeyContext(BaseModel):
    tenant_id: str
    scopes: List[str]

async def get_api_key_context(
    api_key_header: str = Depends(api_key_header),
    session: AsyncSession = Depends(get_session)
) -> AdminAPIKeyContext:
    if not api_key_header:
        # P0-3: If no API Key is provided, do NOT fall back to stub.
        # Strict validation is required for production readiness.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key missing"
        )

    # In a real system, you'd look up the key by hash.
    # Since we store hashes, we have to iterate (inefficient but secure for MVP)
    # OR better: use a prefix-based lookup if the key format allowed it.
    # Here, we will fetch all active keys and verify.
    stmt = select(APIKey).where(APIKey.status == "active")
    result = await session.execute(stmt)
    keys = result.scalars().all()
    
    valid_key = None
    for k in keys:
        if verify_password(api_key_header, k.key_hash):
            valid_key = k
            break
            
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return AdminAPIKeyContext(
        tenant_id=valid_key.tenant_id,
        scopes=valid_key.scopes.split(",") if valid_key.scopes else []
    )

def require_scope(ctx: AdminAPIKeyContext, scope: str):
    if scope not in ctx.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient scope: required {scope}"
        )



# ------------------------------------------------------------
# API key management helpers (used by /api/v1/api-keys endpoints)
# ------------------------------------------------------------
import secrets
from app.constants.api_keys import API_KEY_SCOPES


def validate_scopes(scopes: list) -> None:
    if not isinstance(scopes, list) or any(not isinstance(s, str) for s in scopes):
        raise HTTPException(status_code=422, detail="Invalid scopes")

    invalid = [s for s in scopes if s not in API_KEY_SCOPES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid}")


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns: (full_key, key_prefix, bcrypt_hash)

    Notes:
    - full_key must be returned ONLY once (create endpoint)
    - we store only the hash in DB
    """

    full_key = "sk_" + secrets.token_urlsafe(32)
    key_prefix = full_key[:12]
    key_hash = get_password_hash(full_key)
    return full_key, key_prefix, key_hash
