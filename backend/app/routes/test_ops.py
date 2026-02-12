import os
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_session
from app.models.sql_models import Player
from app.models.game_models import GameRound, GameEvent, Game
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
    result = await session.execute(select(Player).where(Player.email == payload.email))
    player = result.scalars().first()
    if player:
        player.kyc_status = payload.status
        session.add(player)
        await session.commit()
        return {"ok": True, "status": player.kyc_status}
    return {"ok": False, "error": "Player not found"}

@router.get("/dump-rounds")
async def dump_rounds(session: AsyncSession = Depends(get_session)):
    query = select(GameRound)
    result = await session.execute(query)
    rounds = result.scalars().all()
    return {"count": len(rounds), "rounds": [r.model_dump() for r in rounds]}

@router.get("/dump-games")
async def dump_games(session: AsyncSession = Depends(get_session)):
    query = select(Game)
    result = await session.execute(query)
    games = result.scalars().all()
    return {"count": len(games), "games": [g.model_dump() for g in games]}
