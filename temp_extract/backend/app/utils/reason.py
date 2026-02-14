from fastapi import Header, HTTPException, Request
from typing import Optional


async def require_reason(
    request: Request,
    x_reason: Optional[str] = Header(None, alias="X-Reason"),
) -> str:
    """Enforce presence of a reason for mutating actions.

    IMPORTANT:
    - This must NOT declare any additional Body(...) params, otherwise FastAPI
      wraps the endpoint body into { payload: ... } which breaks callers.
    """

    reason = x_reason

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
            detail={"code": "REASON_REQUIRED", "message": "Audit reason is required for this action."},
        )

    return reason
