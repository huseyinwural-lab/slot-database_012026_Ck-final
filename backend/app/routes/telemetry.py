from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.sql_models import TelemetryEvent, Player

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


class TelemetryEventRequest(BaseModel):
    event: str
    payload: dict | None = None
    ts: str | None = None
    session_id: str | None = None
    player_id: str | None = None
    tenant_id: str | None = None


@router.post("/events")
async def capture_event(event: TelemetryEventRequest, session: AsyncSession = Depends(get_session)):
    try:
        tenant_id = event.tenant_id or "default_casino"
        player_id = event.player_id
        if not player_id and event.payload and event.payload.get("player_id"):
            player_id = event.payload.get("player_id")

        if player_id:
            player = await session.exec(select(Player).where(Player.id == player_id))
            player = player.first()
            if player and player.tenant_id:
                tenant_id = player.tenant_id

        record = TelemetryEvent(
            tenant_id=tenant_id,
            player_id=player_id,
            session_id=event.session_id or "unknown",
            event_name=event.event,
            payload=event.payload or {},
        )
        session.add(record)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
    return {"ok": True, "data": {"received": True}}
