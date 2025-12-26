from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_session
from app.models.game_models import Game
from app.models.sql_models import GameConfigVersion, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.core.errors import AppError

router = APIRouter(prefix="/api/v1/games", tags=["game_config"])

@router.get("/{game_id}/config")
async def get_game_config(
    game_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Game).where(Game.id == game_id, Game.tenant_id == tenant_id)
    res = await session.execute(stmt)
    game = res.scalars().first()
    if not game:
        raise HTTPException(404, "Game not found")
    return game.configuration

@router.put("/{game_id}/config")
async def update_game_config(
    game_id: str,
    request: Request,
    config: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Game).where(Game.id == game_id, Game.tenant_id == tenant_id)
    res = await session.execute(stmt)
    game = res.scalars().first()
    if not game:
        raise HTTPException(404, "Game not found")

    # Versioning
    version_entry = GameConfigVersion(
        game_id=game.id,
        tenant_id=game.tenant_id,
        version=str(datetime.now().timestamp()), # Simple versioning
        config_snapshot=game.configuration,
        created_by=current_admin.email
    )
    session.add(version_entry)
    
    # Update
    game.configuration = config
    session.add(game)
    
    await session.commit()
    return {"message": "Config updated"}
