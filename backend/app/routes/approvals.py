from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import ApprovalRequest, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])

@router.get("/requests")
async def get_approval_requests(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(ApprovalRequest).where(ApprovalRequest.tenant_id == tenant_id)
    query = query.where(ApprovalRequest.status == "pending")
    result = await session.execute(query)
    # Direct list return
    return result.scalars().all()

@router.post("/requests/{req_id}/action")
async def action_approval(
    req_id: str,
    request: Request,
    action: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    req = await session.get(ApprovalRequest, req_id)
    if not req or req.tenant_id != tenant_id:
        raise HTTPException(404, "Request not found")
        
    req.status = "approved" if action == "approve" else "rejected"
    session.add(req)
    await session.commit()
    
    return {"message": f"Request {req.status}"}
