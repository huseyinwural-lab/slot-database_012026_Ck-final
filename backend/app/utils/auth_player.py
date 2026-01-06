from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone

from app.core.database import get_session
from app.models.sql_models import Player, PlayerSessionRevocation
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/player/login")

async def get_current_player(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> Player:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        player_id: str = payload.get("sub")
        role: str = payload.get("role")
        iat = payload.get("iat")
        tenant_id = payload.get("tenant_id")

        if player_id is None or role != "player":
            raise credentials_exception

        # P1-E2: iat is mandatory for revocation enforcement
        if iat is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "TOKEN_REVOKED"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception
        
    player = await session.get(Player, player_id)
    if player is None:
        raise credentials_exception
        
    return player
