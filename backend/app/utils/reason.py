from fastapi import Header, Body, HTTPException, Request
from typing import Optional

async def require_reason(
    request: Request,
    x_reason: Optional[str] = Header(None, alias="X-Reason"),
    body_reason: Optional[str] = Body(None, alias="reason")
) -> str:
    """Enforce presence of a reason for mutating actions."""
    reason = x_reason or body_reason
    
    # Check if reason is inside main body payload if not embedded
    if not reason:
        try:
            body = await request.json()
            if isinstance(body, dict):
                reason = body.get("reason")
        except Exception:
            pass

    if not reason:
        raise HTTPException(
            status_code=400,
            detail={"code": "REASON_REQUIRED", "message": "Audit reason is required for this action."}
        )
    return reason
