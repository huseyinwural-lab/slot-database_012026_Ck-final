from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime

# NOTE: This module is MOCKED UI support only and is gated off in prod/staging.

from app.core.database import get_session
from app.models.sql_models import Player, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

from app.utils.permissions import feature_required
from config import settings

router = APIRouter(prefix="/api/v1/kyc", tags=["kyc"])

def _kyc_mock_guard():
    if settings.env in {"prod", "production", "staging"} or not settings.kyc_mock_enabled:
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/dashboard")
async def get_kyc_dashboard(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
    _ = Depends(feature_required("can_manage_kyc")),
):
    _kyc_mock_guard()

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    # Counts
    pending = (await session.execute(select(func.count()).select_from(Player).where(Player.tenant_id == tenant_id, Player.kyc_status == "pending"))).scalar() or 0
    verified = (await session.execute(select(func.count()).select_from(Player).where(Player.tenant_id == tenant_id, Player.kyc_status == "verified"))).scalar() or 0
    rejected = (await session.execute(select(func.count()).select_from(Player).where(Player.tenant_id == tenant_id, Player.kyc_status == "rejected"))).scalar() or 0
    
    # Mock Level Distribution to prevent Frontend Crash
    # Frontend expects: level_distribution: { "Level 1": 10, "Level 2": 5 }
    level_distribution = {
        "Level 1": (await session.execute(select(func.count()).select_from(Player).where(Player.tenant_id == tenant_id))).scalar() or 0,
        "Level 2": 0,
        "Level 3": 0
    }

    return {
        "pending_count": pending, # Frontend uses pending_count, previously mapped to pending_reviews
        "in_review_count": 0, # Mock
        "approved_today": verified,
        "high_risk_pending": 0, # Mock
        "rejected_today": rejected,
        "avg_review_time_mins": 45, # Mock
        "average_time": "2h 15m",
        "verification_rate": "92%",
        "level_distribution": level_distribution
    }

@router.get("/queue")
async def get_kyc_queue(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_manage_kyc")),
    current_admin: AdminUser = Depends(get_current_admin)
):
    _kyc_mock_guard()
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    stmt = select(Player).where(Player.tenant_id == tenant_id, Player.kyc_status == "pending")
    result = await session.execute(stmt)
    players = result.scalars().all()
    
    # Transform to what UI might expect for a "request"
    queue = []
    for p in players:
        queue.append({
            "id": p.id, # Using player ID as request ID for simplicity
            "player_id": p.id,
            "player_username": p.username, # Frontend expects player_username
            "email": p.email,
            "status": p.kyc_status,
            "uploaded_at": p.registered_at, # Proxy
            "risk_score": p.risk_score,
            "type": "identity_document", # Mock
            "file_url": "https://via.placeholder.com/400x300.png?text=Passport",
            # P1-KYC-DL-01: provide a real usable download URL (smallest viable solution).
            # In real systems this would be a signed S3 URL; here we serve a tiny text file.
            "download_url": f"/api/v1/kyc/documents/doc_{p.id}_1/download",
            "documents": [
                {
                    "id": f"doc_{p.id}_1",
                    "type": "passport",
                    "status": "pending",
                    "url": "https://via.placeholder.com/400x300.png?text=Passport",
                    "download_url": f"/v1/kyc/documents/doc_{p.id}_1/download",
                },
                {
                    "id": f"doc_{p.id}_2",
                    "type": "utility_bill",
                    "status": "pending",
                    "url": "https://via.placeholder.com/400x300.png?text=Bill",
                    "download_url": f"/v1/kyc/documents/doc_{p.id}_2/download",
                }
            ]
        })
        
    return queue



@router.get("/documents/{doc_id}/download")
async def download_kyc_document(
    doc_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _ = Depends(feature_required("can_manage_kyc")),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """P1-KYC-DL-01: Provide a real download response.

    In production this would redirect to a signed URL.
    For now we return a small attachment payload to make the UI functional.
    """
    _kyc_mock_guard()

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    _ = tenant_id

    content = f"KYC document mock download for {doc_id}\n"

    headers = {
        "Content-Disposition": f"attachment; filename=kyc_{doc_id}.txt",
        "Content-Type": "text/plain; charset=utf-8",
    }

    from fastapi.responses import Response

    return Response(content=content, media_type="text/plain", headers=headers)

@router.post("/documents/{doc_id}/review")
async def review_document(
    doc_id: str,
    request: Request,
    payload: Dict = Body(...),
    _ = Depends(feature_required("can_manage_kyc")),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    _kyc_mock_guard()

    # Mock implementation since we don't have a Documents table
    # We extract player ID from the mock doc_id (doc_{player_id}_{idx}) or use doc_id as player_id
    player_id = doc_id
    
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    player = await session.get(Player, player_id)
    
    if not player or player.tenant_id != tenant_id:
        return {"message": "Document reviewed (Mock)", "status": payload.get("status")}

    status = payload.get("status") # approved | rejected
    
    if status == "approved":
        player.kyc_status = "verified"
    elif status == "rejected":
        player.kyc_status = "rejected"
        
    session.add(player)
    await session.commit()
    
    return {"message": "Review recorded", "player_status": player.kyc_status}
