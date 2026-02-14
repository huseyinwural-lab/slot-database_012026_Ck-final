from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from typing import Optional, Dict, Any
import hashlib
import json
import uuid

from app.core.database import get_session
from app.models.robot_models import MathAsset
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.services.audit import audit

router = APIRouter(prefix="/api/v1/math-assets", tags=["math_assets"])

# Avoid 307 redirect on trailing slashes (prevents frontend 'Failed' toasts)
router.redirect_slashes = False

@router.get("", response_model=Dict)
async def list_assets(
    page: int = 1,
    limit: int = 20,
    type: Optional[str] = None,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    query = select(MathAsset)
    
    if type and type != "all":
        query = query.where(MathAsset.type == type)
        
    if search:
        query = query.where(MathAsset.ref_key.ilike(f"%{search}%"))
        
    query = query.order_by(MathAsset.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * limit).limit(limit)
    assets = (await session.execute(query)).scalars().all()
    
    return {
        "items": assets,
        "meta": {"total": total, "page": page, "page_size": limit}
    }

@router.post("")
async def create_asset(
    request: Request,
    asset_data: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Upload new math asset.
    Body: { ref_key: str, type: str, content: dict, reason: str }
    """
    reason = request.headers.get("X-Reason") or asset_data.get("reason")
    if not reason:
        raise HTTPException(
            status_code=400,
            detail={"code": "REASON_REQUIRED", "message": "Audit reason is required for this action."}
        )

    ref_key = asset_data.get("ref_key")
    type_ = asset_data.get("type")
    content = asset_data.get("content")
    
    if not all([ref_key, type_, content]):
        raise HTTPException(400, "Missing required fields")
        
    # Check existing
    stmt = select(MathAsset).where(MathAsset.ref_key == ref_key)
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(409, f"Asset {ref_key} already exists. Use Replace/Update.")
        
    content_hash = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    
    asset = MathAsset(
        ref_key=ref_key,
        type=type_,
        content=content,
        content_hash=content_hash
    )
    session.add(asset)
    await session.flush()
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="MATH_ASSET_UPLOAD",
        resource_type="math_asset",
        resource_id=asset.id,
        result="success",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        metadata={"ref_key": ref_key, "hash": content_hash},
        after={"ref_key": ref_key, "type": type_, "hash": content_hash}
    )
    
    await session.commit()
    return asset

@router.post("/{asset_id}/replace")
async def replace_asset(
    request: Request,
    asset_id: str,
    new_content: Dict = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Try header first, then body check (embedded 'new_content' dict doesn't contain reason usually, 
    # but the parent body might if not using embed=True. Here we used embed=True for new_content.
    # So reason must be in Header for replace_asset with this signature, OR we change signature.
    # Let's rely on X-Reason header primarily for this one, or assume client sends it.
    reason = request.headers.get("X-Reason")
    if not reason:
         raise HTTPException(
            status_code=400,
            detail={"code": "REASON_REQUIRED", "message": "Audit reason is required for this action (X-Reason header)."}
        )

    asset = await session.get(MathAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
        
    old_hash = asset.content_hash
    new_hash = hashlib.sha256(json.dumps(new_content, sort_keys=True).encode()).hexdigest()
    
    asset.content = new_content
    asset.content_hash = new_hash
    
    session.add(asset)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=current_admin.tenant_id,
        action="MATH_ASSET_REPLACE",
        resource_type="math_asset",
        resource_id=asset.id,
        result="success",
        reason=reason,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
        metadata={"old_hash": old_hash, "new_hash": new_hash},
        before={"hash": old_hash},
        after={"hash": new_hash},
        diff={"hash": {"from": old_hash, "to": new_hash}}
    )
    
    await session.commit()
    return asset
