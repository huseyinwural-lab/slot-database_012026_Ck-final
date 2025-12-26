from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import List, Optional, Dict
import hashlib
import json
import uuid
from datetime import datetime

from app.core.database import get_session
from app.models.robot_models import RobotDefinition
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.services.audit import audit

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
    query = select(RobotDefinition)
    
    if search:
        query = query.where(RobotDefinition.name.ilike(f"%{search}%"))
    
    if is_active is not None:
        query = query.where(RobotDefinition.is_active == is_active)
        
    # motor_type filtering would require JSON query on config, unlikely for MVP sqlite/simple
    # Skipping deep JSON filter for now unless explicitly needed
    
    query = query.order_by(RobotDefinition.created_at.desc())
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * limit).limit(limit)
    robots = (await session.execute(query)).scalars().all()
    
    return {
        "items": robots,
        "meta": {"total": total, "page": page, "page_size": limit}
    }

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
    robot_id: str,
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
        request_id=str(uuid.uuid4()),
        actor_user_id=current_admin.id,
        tenant_id=current_admin.tenant_id,
        action="ROBOT_TOGGLE",
        resource_type="robot",
        resource_id=robot.id,
        result="success",
        details={"old_state": old_state, "new_state": robot.is_active}
    )
    
    await session.commit()
    return robot

@router.post("/{robot_id}/clone")
async def clone_robot(
    robot_id: str,
    name_suffix: str = Body(" (Cloned)", embed=True),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    original = await session.get(RobotDefinition, robot_id)
    if not original:
        raise HTTPException(404, "Robot not found")
        
    new_robot = RobotDefinition(
        name=f"{original.name}{name_suffix}",
        config=original.config,
        config_hash=original.config_hash,
        is_active=False # Default to inactive
    )
    
    session.add(new_robot)
    await session.flush()
    
    # Audit
    await audit.log_event(
        session=session,
        request_id=str(uuid.uuid4()),
        actor_user_id=current_admin.id,
        tenant_id=current_admin.tenant_id,
        action="ROBOT_CLONE",
        resource_type="robot",
        resource_id=new_robot.id,
        result="success",
        details={"original_id": original.id}
    )
    
    await session.commit()
    return new_robot
