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
        

    # P1-E2: session revocation enforcement (check before status so old tokens get 401 TOKEN_REVOKED)
    stmt = select(PlayerSessionRevocation).where(
        PlayerSessionRevocation.tenant_id == tenant_id,
        PlayerSessionRevocation.player_id == player_id,
    )
    rev = (await session.execute(stmt)).scalars().first()
    if rev and rev.revoked_at:
        try:
            token_iat = datetime.fromtimestamp(int(iat) / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "TOKEN_REVOKED"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        rev_at = rev.revoked_at
        if getattr(rev_at, "tzinfo", None) is not None:
            rev_at = rev_at.astimezone(timezone.utc).replace(tzinfo=None)
        rev_at = rev_at.replace(microsecond=0)

        # Treat tokens issued at or before revocation moment as revoked (iat has second precision)
        if token_iat <= rev_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "TOKEN_REVOKED"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    # P1-E3: suspended players cannot access protected endpoints
    if getattr(player, "status", None) == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PLAYER_SUSPENDED"},
        )

    return player
