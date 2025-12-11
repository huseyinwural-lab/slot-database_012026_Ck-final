from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.utils.auth import AdminAPIKeyContext, get_api_key_context, require_scope


router = APIRouter(prefix="/api/v1/robot", tags=["robot"])


class RobotRoundRequest(BaseModel):
    game_types: List[str] = ["slot", "crash", "dice"]
    rounds: int = 50
    tenant_id: Optional[str] = None


class RobotRoundResponse(BaseModel):
    status: str
    tenant_id: str
    game_types: List[str]
    rounds: int
    scopes: List[str]


@router.post("/round", response_model=RobotRoundResponse)
async def robot_round(
    payload: RobotRoundRequest,
    api_ctx: AdminAPIKeyContext = Depends(get_api_key_context),
):
    """Minimal robot backend endpoint.

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

    # Şimdilik sadece context'i doğrulayan hafif bir endpoint.
    # İleride gerçek round/senaryo tetikleme mantığı buraya taşınabilir.
    return RobotRoundResponse(
        status="ok",
        tenant_id=api_ctx.tenant_id,
        game_types=payload.game_types,
        rounds=payload.rounds,
        scopes=api_ctx.scopes,
    )
