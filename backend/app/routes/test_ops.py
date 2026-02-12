import os
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_session
from app.models.sql_models import Player
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/test", tags=["test-ops"])

class KYCUpdate(BaseModel):
    email: str
    status: str = "verified"

# Allow in Mock/Dev mode only
MOCK_MODE = os.getenv("MOCK_EXTERNAL_SERVICES", "false").lower() == "true"

@router.post("/set-kyc")
async def set_kyc_status(
    payload: KYCUpdate,
    session: AsyncSession = Depends(get_session)
):
    # Security check: only in mock mode or specific env
    # For now, simplistic
    result = await session.execute(select(Player).where(Player.email == payload.email))
    player = result.scalars().first()
    if player:
        player.kyc_status = payload.status
        session.add(player)
        await session.commit()
        return {"ok": True, "status": player.kyc_status}
    return {"ok": False, "error": "Player not found"}
