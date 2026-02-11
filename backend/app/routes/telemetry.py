from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


class TelemetryEvent(BaseModel):
    event: str
    payload: dict | None = None
    ts: str | None = None


@router.post("/events")
async def capture_event(event: TelemetryEvent):
    return {"ok": True, "data": {"received": True}}
