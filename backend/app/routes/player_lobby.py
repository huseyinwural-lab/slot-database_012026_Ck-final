from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.game_models import Game
from app.core.database import get_session
from app.utils.auth_player import get_current_player
from app.models.sql_models import Player

router = APIRouter(prefix="/api/v1/player", tags=["player_lobby"])

@router.get("/games")
async def get_lobby_games(request: Request, session: AsyncSession = Depends(get_session)):
    tenant_id = request.headers.get("X-Tenant-ID", "default_casino")
    
    stmt = select(Game).where(Game.tenant_id == tenant_id).where(Game.status == "active").limit(100)
    result = await session.execute(stmt)
    games = result.scalars().all()
    
    return {
        "items": games,
        "meta": {"total": len(games)}
    }

@router.get("/games/{game_id}/launch")
async def launch_game(game_id: str, current_player: Player = Depends(get_current_player)):
    if not current_player.email_verified or not current_player.sms_verified:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "AUTH_UNVERIFIED", "message": "Verification required"},
        )

    return {
        "launch_url": f"http://localhost:8001/api/v1/player/mock-game/{game_id}",
        "method": "iframe"
    }

@router.get("/mock-game/{game_id}")
async def mock_game_ui(game_id: str):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=f"<h1>Playing Game {game_id} (SQL Backend)</h1>", status_code=200)
