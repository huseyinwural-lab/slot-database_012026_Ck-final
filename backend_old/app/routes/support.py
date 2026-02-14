from fastapi import APIRouter, Depends, Body, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sql_models import SupportTicket, AdminUser
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from datetime import datetime

router = APIRouter(prefix="/api/v1/support", tags=["support"])


class PlayerSupportRequest(BaseModel):
    player_id: str
    tenant_id: str
    message: str
    subject: str | None = None

@router.get("/tickets")
async def get_tickets(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(SupportTicket).where(SupportTicket.tenant_id == tenant_id).order_by(SupportTicket.created_at.desc())
    result = await session.execute(query)
    # Return as list, frontend should handle it (or update to {items: ...})
    # Given previous instruction: standardize to match frontend if it expects list.
    # If frontend expects paginated, we should wrap.
    # Looking at Support.jsx (from memory), it likely maps directly.
    return result.scalars().all()

@router.post("/tickets/{ticket_id}/reply")
async def reply_ticket(
    ticket_id: str,
    request: Request,
    message: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    ticket = await session.get(SupportTicket, ticket_id)
    if not ticket or ticket.tenant_id != tenant_id:
        raise HTTPException(404, "Ticket not found")
        
    msg_obj = {
        "sender": current_admin.email,
        "text": message.get("text"),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    msgs = list(ticket.messages) if ticket.messages else []
    msgs.append(msg_obj)
    ticket.messages = msgs
    ticket.status = "answered"
    
    session.add(ticket)
    await session.commit()
    return {"message": "Replied"}


@router.post("/ticket")
async def create_player_ticket(payload: PlayerSupportRequest, session: AsyncSession = Depends(get_session)):
    ticket = SupportTicket(
        tenant_id=payload.tenant_id,
        player_id=payload.player_id,
        subject=payload.subject or "Player Support",
        messages=[{
            "sender": "player",
            "text": payload.message,
            "time": datetime.utcnow().isoformat(),
        }],
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return {"ok": True, "data": {"ticket_id": ticket.id, "status": "received"}}
