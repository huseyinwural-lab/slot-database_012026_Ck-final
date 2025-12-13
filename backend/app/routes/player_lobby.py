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
    """
    # For MVP, mock the launch URL
    # We can point to a simple visual demo or just a placeholder
    return {
        "launch_url": f"https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&controls=0&showinfo=0&mute=1", # Rickroll as placeholder :) or better yet:
        #"launch_url": "https://scratch.mit.edu/projects/embed/123456/?autostart=true", # Scratch game?
        # Let's use a professional looking placeholder or a static HTML we serve.
        # Ideally, we return a simple static page hosted by us.
        "launch_url": f"http://localhost:8001/api/v1/player/mock-game/{game_id}",
        "method": "iframe"
    }

@router.get("/mock-game/{game_id}")
async def mock_game_ui(game_id: str):
    from fastapi.responses import HTMLResponse
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock Game</title>
        <style>
            body {{ background: #1a1a1a; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: sans-serif; }}
            .slot {{ border: 4px solid gold; padding: 20px; border-radius: 10px; background: #333; text-align: center; }}
            .reels {{ display: flex; gap: 10px; margin: 20px 0; }}
            .reel {{ width: 80px; height: 100px; background: white; color: black; font-size: 40px; display: flex; align-items: center; justify-content: center; border-radius: 5px; }}
            button {{ background: #e91e63; color: white; border: none; padding: 15px 30px; font-size: 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }}
            button:active {{ transform: scale(0.95); }}
        </style>
    </head>
    <body>
        <div class="slot">
            <h1>🎰 SUPER MOCK SLOT 🎰</h1>
            <div class="reels">
                <div class="reel" id="r1">🍒</div>
                <div class="reel" id="r2">🍋</div>
                <div class="reel" id="r3">🍇</div>
            </div>
            <button onclick="spin()">SPIN</button>
            <p>Game ID: {game_id}</p>
        </div>
        <script>
            function spin() {{
                const symbols = ['🍒', '🍋', '🍇', '💎', '7️⃣'];
                document.getElementById('r1').innerText = symbols[Math.floor(Math.random() * symbols.length)];
                document.getElementById('r2').innerText = symbols[Math.floor(Math.random() * symbols.length)];
                document.getElementById('r3').innerText = symbols[Math.floor(Math.random() * symbols.length)];
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

