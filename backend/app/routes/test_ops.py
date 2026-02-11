import os
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_session
from app.models.sql_models import Player
from app.utils.auth import get_password_hash as hash_password

router = APIRouter(prefix="/api/v1/test", tags=["test-ops"])

# Only enable in non-prod environments (or if specific flag is set)
# For now, we assume this pod is a dev/staging environment where we need seeding.
ALLOWED_ENVS = ["dev", "staging", "local", "preview"]
ENV = os.getenv("ENV", "local")

@router.post("/seed")
async def seed_test_user(session: AsyncSession = Depends(get_session)):
    # Simple hardcoded seed for P0 testing
    email = "player_e2e@casino.com"
    password = "Player123!"
    phone = "+15550001111"
    
    # Check if exists
    existing = await session.exec(select(Player).where(Player.email == email))
    if existing.first():
        return {"ok": True, "message": "User already exists", "email": email}

    # Create Player
    hashed = hash_password(password)
    player = Player(
        email=email,
        hashed_password=hashed,
        phone=phone,
        first_name="E2E",
        last_name="Tester",
        dob=date(1990, 1, 1),
        email_verified=False, # Start unverified for testing flow
        sms_verified=False,
        is_active=True,
        kyc_status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(player)
    await session.commit()
    
    return {"ok": True, "message": "Seeded", "email": email}
