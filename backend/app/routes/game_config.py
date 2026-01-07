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
from app.models.robot_models import GameRobotBinding, RobotDefinition
from app.services.audit import audit
import uuid

router = APIRouter(prefix="/api/v1/games", tags=["game_config"])

@router.get("/{game_id}/config")
async def get_game_config(
    game_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """P2-GO-BE-01: Read-only Game Config snapshot.

    Goal: Allow the Config modal to open deterministically without failing even when
    provider config is not available.

    IMPORTANT: This endpoint is intentionally **read-only**. UI should disable save
    actions when `is_read_only=true`.
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Game).where(Game.id == game_id, Game.tenant_id == tenant_id)
    res = await session.execute(stmt)
    game = res.scalars().first()
    if not game:
        raise HTTPException(404, "Game not found")

    cfg = game.configuration if isinstance(game.configuration, dict) else {}

    # Minimal + safe payload: nulls are intentional when config is not available.
    return {
        "game_id": game.id,
        "name": game.name,
        "provider": getattr(game, "provider_id", None) or game.provider,
        "category": game.category,
        "status": game.status or ("active" if getattr(game, "is_active", False) else "inactive"),
        "rtp": cfg.get("rtp") if isinstance(cfg.get("rtp"), (int, float)) else None,
        "volatility": cfg.get("volatility") if isinstance(cfg.get("volatility"), (str, int, float)) else None,
        "limits": cfg.get("limits") if isinstance(cfg.get("limits"), dict) else None,
        "features": cfg.get("features") if isinstance(cfg.get("features"), list) else [],
        "is_read_only": True,
    }

@router.put("/{game_id}/config")
async def update_game_config(
    game_id: str,
    request: Request,
    config: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    reason = request.headers.get("X-Reason") or config.get("reason")
    if not reason:
        raise HTTPException(
            status_code=400,
            detail={"code": "REASON_REQUIRED", "message": "Audit reason is required for this action."}
        )

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Game).where(Game.id == game_id, Game.tenant_id == tenant_id)
    res = await session.execute(stmt)
    game = res.scalars().first()
    if not game:
        raise HTTPException(404, "Game not found")

    old_config = game.configuration

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
    
    # Audit
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="GAME_CONFIG_PUBLISH",
        resource_type="game",
        resource_id=game.id,
        result="success",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        before=old_config,
        after=config
    )

    await session.commit()
    return {"message": "Config updated"}

@router.get("/{game_id}/robot")
async def get_game_robot(
    game_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(GameRobotBinding, RobotDefinition).join(RobotDefinition).where(GameRobotBinding.game_id == game_id)
    # We want the ACTIVE binding
    stmt = stmt.where(GameRobotBinding.is_enabled.is_(True))
    res = await session.execute(stmt)
    row = res.first()
    
    if not row:
        return {} # Empty object if no binding
        
    binding, robot = row
    return {
        "binding_id": binding.id,
        "robot_id": robot.id,
        "robot_name": robot.name,
        "config_hash": robot.config_hash,
        "is_active": robot.is_active,
        "effective_from": binding.effective_from
    }

@router.post("/{game_id}/robot")
async def bind_game_robot(
    request: Request,
    game_id: str,
    payload: Dict[str, Any] = Body(...), # { robot_id: str }
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    reason = request.headers.get("X-Reason") or payload.get("reason")
    if not reason:
        raise HTTPException(
            status_code=400,
            detail={"code": "REASON_REQUIRED", "message": "Audit reason is required for this action."}
        )

    robot_id = payload.get("robot_id")
    if not robot_id:
        raise HTTPException(400, "robot_id required")
        
    # Check robot exists
    robot = await session.get(RobotDefinition, robot_id)
    if not robot:
        raise HTTPException(404, "Robot not found")
    if not robot.is_active:
        raise HTTPException(409, "Robot is not active")
        
    # Disable old binding
    stmt = select(GameRobotBinding).where(GameRobotBinding.game_id == game_id, GameRobotBinding.is_enabled.is_(True))
    old_binding = (await session.execute(stmt)).scalars().first()
    old_robot_id = old_binding.robot_id if old_binding else None
    
    if old_binding:
        old_binding.is_enabled = False
        session.add(old_binding)
        
    # Create new binding
    new_binding = GameRobotBinding(
        tenant_id=current_admin.tenant_id,
        game_id=game_id,
        robot_id=robot_id,
        is_enabled=True
    )
    session.add(new_binding)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="GAME_ROBOT_BIND",
        resource_type="game",
        resource_id=game_id,
        result="success",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        details={"robot_id": robot_id},
        before={"robot_id": old_robot_id},
        after={"robot_id": robot_id}
    )
    
    await session.commit()
    return {"message": "Robot bound successfully", "binding_id": new_binding.id}
