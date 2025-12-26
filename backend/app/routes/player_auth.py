from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone, timedelta
import uuid

from app.models.sql_models import Player
from app.services.affiliate_engine import AffiliateEngine
from app.core.database import get_session
from app.utils.auth import get_password_hash, verify_password, create_access_token
from app.schemas.player import PlayerPublic

router = APIRouter(prefix="/api/v1/auth/player", tags=["player_auth"])

@router.post("/register")
async def register_player(payload: dict = Body(...), session: AsyncSession = Depends(get_session)):
    email = payload.get("email")
    tenant_id = payload.get("tenant_id", "default_casino")
    
    # Check exists
    stmt = select(Player).where(Player.email == email).where(Player.tenant_id == tenant_id)
    res = await session.execute(stmt)
    existing = res.scalars().first()
    if existing:
        raise HTTPException(400, "Player exists")
        
    password = payload.get("password")
    if not password or len(str(password)) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Hash password
    hashed_password = get_password_hash(password)
    
    player = Player(
        email=email,
        username=payload.get("username"),
        tenant_id=tenant_id,
        password_hash=hashed_password,
        registered_at=datetime.utcnow()
    )
    
    session.add(player)
    await session.commit()
    await session.refresh(player) # Need ID for attribution

    # Affiliate Attribution
    referral_code = payload.get("referral_code") or payload.get("ref_code")
    if referral_code:
        aff_engine = AffiliateEngine()
        await aff_engine.attribute_player(session, player.id, tenant_id, referral_code)
        await session.commit()
    
    return {"message": "Registered", "player_id": player.id}

@router.post("/login")
async def login_player(payload: dict = Body(...), session: AsyncSession = Depends(get_session)):
    email = payload.get("email")
    tenant_id = payload.get("tenant_id", "default_casino")
    
    stmt = select(Player).where(Player.email == email).where(Player.tenant_id == tenant_id)
    res = await session.execute(stmt)
    player = res.scalars().first()
    
    if not player or not verify_password(payload.get("password"), player.password_hash):
        raise HTTPException(401, "Invalid credentials")
        
    token = create_access_token(
        data={"sub": player.id, "role": "player", "tenant_id": tenant_id},
        expires_delta=timedelta(days=7)
    )
    
    pub = PlayerPublic.model_validate(player)
    return {
        "access_token": token,
        "user": {
            "id": pub.id,
            "username": pub.username,
            "balance_real": pub.balance_real,
            "tenant_id": pub.tenant_id,
        }
    }
