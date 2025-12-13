from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.sql_models import AdminUser
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

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
    expire = datetime.now(timezone.utc) + expires_delta
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
    result = await session.exec(statement)
    admin = result.first()
    
    if admin is None:
        raise credentials_exception
    return admin

async def get_admin_by_email(email: str, session: AsyncSession) -> AdminUser | None:
    statement = select(AdminUser).where(AdminUser.email == email)
    result = await session.exec(statement)
    return result.first()

from pydantic import BaseModel
from typing import List

class AdminAPIKeyContext(BaseModel):
    tenant_id: str
    scopes: List[str]

async def get_api_key_context(token: str = Depends(oauth2_scheme)) -> AdminAPIKeyContext:
    # Stub implementation for now to satisfy imports
    # In a real scenario, this would validate an API Key from header
    return AdminAPIKeyContext(tenant_id="default_casino", scopes=["robot.run"])

def require_scope(ctx: AdminAPIKeyContext, scope: str):
    if scope not in ctx.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient scope"
        )