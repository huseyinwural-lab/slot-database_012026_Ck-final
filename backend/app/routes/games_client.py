from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from app.core.database import get_session
from app.models.game_models import Game, GameSession
from app.schemas.game_schemas import GameLaunchRequest, GameLaunchResponse
from app.utils.auth_player import get_current_player
from app.models.sql_models import Player
import uuid

router = APIRouter(prefix="/api/v1/games", tags=["games"])

@router.get("/", response_model=List[Game])
async def list_games(
    tenant_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Game).where(Game.is_active == True)
    if tenant_id:
        stmt = stmt.where(Game.tenant_id == tenant_id)
    return (await session.execute(stmt)).scalars().all()

@router.post("/launch", response_model=GameLaunchResponse)
async def launch_game(
    body: GameLaunchRequest,
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    game = await session.get(Game, body.game_id)
    if not game:
        raise HTTPException(404, "Game not found")
        
    # Create Session
    session_id = str(uuid.uuid4())
    # Provider Session ID might be different, but for mock we use same
    prov_sess_id = f"sess-{uuid.uuid4().hex[:12]}"
    
    new_session = GameSession(
        id=session_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        game_id=game.id,
        provider_session_id=prov_sess_id,
        currency=body.currency
    )
    session.add(new_session)
    await session.commit()
    
    # URL construction
    # For real provider, we would call their API to get a URL.
    # For mock, we direct to our own GameRoom with session_id
    launch_url = f"/game/{session_id}"
    
    return {"url": launch_url, "session_id": session_id}
