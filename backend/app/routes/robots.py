from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import Optional, Dict
import hashlib
import json
import uuid
from datetime import datetime

from app.core.database import get_session
from app.models.robot_models import RobotDefinition
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.services.audit import audit
from app.utils.reason import require_reason

router = APIRouter(prefix="/api/v1/robots", tags=["robots"])

@router.get("/", response_model=Dict)
async def list_robots(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    motor_type: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    _ = session, current_admin, search, is_active, motor_type
    return {
        "items": [],
        "meta": {"total": 0, "page": page, "page_size": limit}
    }


@router.get("/status")
async def robots_status(
    current_admin: AdminUser = Depends(get_current_admin),
):
    _ = current_admin
    return {"status": "idle", "active_bots": 0}

@router.get("/{robot_id}", response_model=RobotDefinition)
async def get_robot(
    robot_id: str,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    robot = await session.get(RobotDefinition, robot_id)
    if not robot:
        raise HTTPException(404, "Robot not found")
    return robot

@router.post("/{robot_id}/toggle")
async def toggle_robot(
    request: Request,
    robot_id: str,
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    robot = await session.get(RobotDefinition, robot_id)
    if not robot:
        raise HTTPException(404, "Robot not found")
    
    old_state = robot.is_active
    robot.is_active = not robot.is_active
    robot.updated_at = datetime.utcnow()
    
    session.add(robot)
    
    # Audit
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="ROBOT_TOGGLE",
        resource_type="robot",
        resource_id=robot.id,
        result="success",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        before={"is_active": old_state},
        after={"is_active": robot.is_active},
        diff={"is_active": {"from": old_state, "to": robot.is_active}}
    )
    
    await session.commit()
    return robot

@router.post("/{robot_id}/clone")
async def clone_robot(
    request: Request,
    robot_id: str,
    name_suffix: str = Body(" (Cloned)", embed=True),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    original = await session.get(RobotDefinition, robot_id)
    if not original:
        raise HTTPException(404, "Robot not found")
        
    # Clone should be usable for immediate binding in E2E:
    # preserve the full config so slot math assets remain resolvable.
    robot_config = original.config or {}
    robot_hash = original.config_hash
    if not robot_hash:
        robot_hash = hashlib.sha256(json.dumps(robot_config, sort_keys=True).encode()).hexdigest()

    new_robot = RobotDefinition(
        name=f"{original.name}{name_suffix}",
        config=robot_config,
        config_hash=robot_hash,
        is_active=False  # Default to inactive
    )
    
    session.add(new_robot)
    await session.flush()
    
    # Audit
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="ROBOT_CLONE",
        resource_type="robot",
        resource_id=new_robot.id,
        result="success",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        metadata={"original_robot_id": original.id},
        after={"name": new_robot.name, "config_hash": new_robot.config_hash}
    )
    
    await session.commit()
    return new_robot
