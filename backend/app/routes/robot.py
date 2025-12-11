from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

from app.utils.auth import AdminAPIKeyContext, get_api_key_context, require_scope
from app.services.robot_orchestrator import RobotOrchestrator
from app.routes.core import get_db


router = APIRouter(prefix="/api/v1/robot", tags=["robot"])


class RobotRoundRequest(BaseModel):
    game_types: List[str] = ["slot", "crash", "dice"]
    rounds: int = 50
    tenant_id: Optional[str] = None


class RobotRoundSummary(BaseModel):
    game_type: str
    game_id: Optional[str]
    rounds: int
    errors: int
    avg_rtp: Optional[float] = None
    avg_duration_ms: Optional[float] = None


class RobotRoundResponse(BaseModel):
    status: str
    tenant_id: str
    total_rounds: int
    results: List[RobotRoundSummary]


@router.post("/round", response_model=RobotRoundResponse)
async def robot_round(
    payload: RobotRoundRequest,
    api_ctx: AdminAPIKeyContext = Depends(get_api_key_context),
):
    """Robot Orchestrator backend endpoint.

    - Auth: API key zorunlu
    - Scope: robot.run şart
    - Tenant: API key'in tenant_id'si gerçektir; payload.tenant_id varsa cross-check edilir.
    """
    require_scope(api_ctx, "robot.run")

    if payload.tenant_id and payload.tenant_id != api_ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "TENANT_MISMATCH",
                "api_key_tenant": api_ctx.tenant_id,
                "requested_tenant": payload.tenant_id,
            },
        )

    db = get_db()

    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        orchestrator = RobotOrchestrator(db, client)
        summary = await orchestrator.run_rounds(
            tenant_id=api_ctx.tenant_id,
            game_types=payload.game_types,
            rounds=payload.rounds,
        )

    return RobotRoundResponse(
        status="ok",
        tenant_id=summary["tenant_id"],
        total_rounds=summary["total_rounds"],
        results=[RobotRoundSummary(**r) for r in summary["results"]],
    )
