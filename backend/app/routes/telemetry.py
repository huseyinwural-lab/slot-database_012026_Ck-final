from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.sql_models import TelemetryEvent, Player

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


TelemetryEventName = Literal[
    "register_success",
    "login_success",
    "email_verified",
    "sms_verified",
    "lobby_loaded",
    "game_launch_click",
    "game_launch_success",
    "game_launch_fail",
]


class TelemetryEventRequest(BaseModel):
    event: TelemetryEventName
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


@router.get("/kpi/game-start-rate")
async def game_start_rate(session: AsyncSession = Depends(get_session)):
    since = datetime.utcnow() - timedelta(days=1)
    lobby_count = await session.exec(
        select(func.count()).select_from(TelemetryEvent).where(
            TelemetryEvent.event_name == "lobby_loaded",
            TelemetryEvent.created_at >= since,
        )
    )
    launch_count = await session.exec(
        select(func.count()).select_from(TelemetryEvent).where(
            TelemetryEvent.event_name == "game_launch_success",
            TelemetryEvent.created_at >= since,
        )
    )
    lobby_value = lobby_count.first() or 0
    launch_value = launch_count.first() or 0
    rate = (launch_value / lobby_value) if lobby_value else 0
    return {
        "ok": True,
        "data": {
            "since": since.isoformat(),
            "lobby_loaded": lobby_value,
            "game_launch_success": launch_value,
            "game_start_rate": rate,
        },
    }
