from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone, timedelta
import uuid

from app.models.sql_models import Player
from app.core.database import get_session
from app.utils.auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth/player", tags=["player_auth"])

@router.post("/register")
async def register_player(payload: dict = Body(...), session: AsyncSession = Depends(get_session)):
    email = payload.get("email")
    tenant_id = payload.get("tenant_id", "default_casino")
    
    # Check exists
    stmt = select(Player).where(Player.email == email).where(Player.tenant_id == tenant_id)
    existing = (await session.exec(stmt)).first()
    if existing:
        raise HTTPException(400, "Player exists")
        
    player = Player(
        email=email,
        username=payload.get("username"),
        tenant_id=tenant_id,
        password_hash=get_password_hash(payload.get("password")),
        registered_at=datetime.now(timezone.utc)
    )
    
    session.add(player)
    await session.commit()
    
    return {"message": "Registered", "player_id": player.id}

@router.post("/login")
async def login_player(payload: dict = Body(...), session: AsyncSession = Depends(get_session)):
    email = payload.get("email")
    tenant_id = payload.get("tenant_id", "default_casino")
    
    stmt = select(Player).where(Player.email == email).where(Player.tenant_id == tenant_id)
    player = (await session.exec(stmt)).first()
    
    if not player or not verify_password(payload.get("password"), player.password_hash):
        raise HTTPException(401, "Invalid credentials")
        
    token = create_access_token(
        data={"sub": player.id, "role": "player", "tenant_id": tenant_id},
        expires_delta=timedelta(days=7)
    )
    
    return {
        "access_token": token,
        "user": {
            "id": player.id,
            "username": player.username,
            "balance_real": player.balance_real
        }
    }
