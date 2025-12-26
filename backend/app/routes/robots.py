from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import json
import hashlib

from app.core.database import get_session
from app.models.robot_models import RobotDefinition, MathAsset, GameRobotBinding
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.services.audit import audit
from app.utils.permissions import feature_required

router = APIRouter(prefix="/api/v1/robots", tags=["robots"])

# --- ROBOTS ---

@router.get("/", response_model=List[RobotDefinition])
async def list_robots(
    active_only: bool = False,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")), # Feature Gate
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(RobotDefinition)
    if active_only:
        stmt = stmt.where(RobotDefinition.is_active == True)
    stmt = stmt.order_by(RobotDefinition.created_at.desc())
    return (await session.execute(stmt)).scalars().all()

@router.get("/{robot_id}", response_model=RobotDefinition)
async def get_robot(
    robot_id: str,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    robot = await session.get(RobotDefinition, robot_id)
    if not robot:
        raise HTTPException(404, "Robot not found")
    return robot

@router.post("/{robot_id}/toggle")
async def toggle_robot(
    robot_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    robot = await session.get(RobotDefinition, robot_id)
    if not robot:
        raise HTTPException(404, "Robot not found")
        
    prev = robot.is_active
    robot.is_active = not robot.is_active
    session.add(robot)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", "unknown"),
        actor_user_id=current_admin.id,
        tenant_id=current_admin.tenant_id,
        action="ROBOT_TOGGLE",
        resource_type="robot",
        resource_id=robot.id,
        result="success",
        details={"before": prev, "after": robot.is_active}
    )
    
    await session.commit()
    return {"status": "success", "is_active": robot.is_active}

@router.post("/{robot_id}/clone")
async def clone_robot(
    robot_id: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    source = await session.get(RobotDefinition, robot_id)
    if not source:
        raise HTTPException(404, "Source robot not found")
        
    new_name = payload.get("name", f"{source.name} (Copy)")
    
    new_robot = RobotDefinition(
        name=new_name,
        schema_version=source.schema_version,
        config=source.config, # Deep copy recommended if mutable
        config_hash=source.config_hash,
        is_active=False
    )
    session.add(new_robot)
    await session.flush()
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", "unknown"),
        actor_user_id=current_admin.id,
        tenant_id=current_admin.tenant_id,
        action="ROBOT_CLONE",
        resource_type="robot",
        resource_id=new_robot.id,
        result="success",
        details={"source_id": source.id}
    )
    
    await session.commit()
    await session.refresh(new_robot)
    return new_robot

# --- MATH ASSETS ---

@router.get("/assets", response_model=List[MathAsset])
async def list_assets(
    type: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(MathAsset)
    if type:
        stmt = stmt.where(MathAsset.type == type)
    stmt = stmt.order_by(MathAsset.created_at.desc())
    return (await session.execute(stmt)).scalars().all()

# --- BINDING ---

@router.get("/binding/{game_id}")
async def get_game_binding(
    game_id: str,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    stmt = select(GameRobotBinding).where(GameRobotBinding.game_id == game_id).order_by(GameRobotBinding.created_at.desc())
    binding = (await session.execute(stmt)).scalars().first()
    
    if not binding:
        return {"robot_id": None}
        
    # Get robot details
    robot = await session.get(RobotDefinition, binding.robot_id)
    
    return {
        "binding_id": binding.id,
        "robot_id": binding.robot_id,
        "is_enabled": binding.is_enabled,
        "robot_name": robot.name if robot else "Unknown",
        "robot_active": robot.is_active if robot else False
    }

@router.post("/binding/{game_id}")
async def set_game_binding(
    game_id: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_use_game_robot")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    robot_id = payload.get("robot_id")
    is_enabled = payload.get("is_enabled", True)
    
    # Verify Robot
    robot = await session.get(RobotDefinition, robot_id)
    if not robot:
        raise HTTPException(404, "Robot not found")
        
    # Create new binding record (History preserved by creating new rows)
    binding = GameRobotBinding(
        tenant_id=current_admin.tenant_id,
        game_id=game_id,
        robot_id=robot_id,
        is_enabled=is_enabled
    )
    session.add(binding)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", "unknown"),
        actor_user_id=current_admin.id,
        tenant_id=current_admin.tenant_id,
        action="GAME_ROBOT_BIND",
        resource_type="game_robot_binding",
        resource_id=binding.id,
        result="success",
        details={"game_id": game_id, "robot_id": robot_id}
    )
    
    await session.commit()
    return binding
