from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from app.models.core import Game, GameConfig
from app.core.database import db_wrapper
from app.models.common import PaginatedResponse
from app.utils.pagination import get_pagination_params

router = APIRouter(prefix="/api/v1/player", tags=["player_lobby"])

@router.get("/games", response_model=PaginatedResponse[Game])
async def get_lobby_games(request: Request):
    """
    Public endpoint for lobby games.
    Respects Tenant ID header.
    Only returns active games.
    """
    db = db_wrapper.db
    
    # Tenant Resolution
    tenant_id = request.headers.get("X-Tenant-ID", "default_casino")
    
    query = {
        "tenant_id": tenant_id,
        "status": "active" # Only active games
    }
    
    # Projection to hide sensitive config
    projection = {
        "id": 1, "name": 1, "provider": 1, "category": 1, "image_url": 1, 
        "tags": 1, "slug": 1, "_id": 0
    }
    
    cursor = db.games.find(query, projection).limit(50)
    games = await cursor.to_list(50)
    
    return {
        "items": games,
        "meta": {"total": len(games), "page": 1, "page_size": 50}
    }

@router.get("/games/{game_id}/launch")
async def launch_game(game_id: str, request: Request):
    """
    Generates launch URL/Token for a game.
    Requires Player Auth (TODO: Add Depends(get_current_player))
    """
    # For MVP, mock the launch URL
    return {
        "launch_url": f"https://demo-games.provider.com/launch?game_id={game_id}&token=mock_session_token",
        "method": "iframe"
    }
