from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from app.core.database import get_session
from app.models.game_models import Game, GameSession
from app.schemas.game_schemas import GameLaunchRequest, GameLaunchResponse
from app.utils.auth_player import get_current_player
from app.models.sql_models import Player
import uuid

router = APIRouter(prefix="/api/v1/player/client-games", tags=["games"])

@router.get("/", response_model=List[Game])
async def list_games(
    tenant_id: Optional[str] = None,
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    # Tenant filtering logic based on player's tenant
    stmt = select(Game).where(Game.is_active == True)
    
    # In multi-tenant, player only sees games assigned to their tenant
    # Assuming all games are global for MVP unless filtered
    stmt = stmt.where(Game.tenant_id == current_player.tenant_id)
    
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
        
    # Tenant check
    if game.tenant_id != current_player.tenant_id:
        raise HTTPException(403, "Game not available")

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
    # For mock, direct to our Frontend Route
    launch_url = f"/game/{session_id}"
    
    return {"url": launch_url, "session_id": session_id}
