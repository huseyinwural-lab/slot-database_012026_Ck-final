from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Any, Dict, Optional

class AppError(HTTPException):
    def __init__(
        self, 
        error_code: str, 
        message: str, 
        status_code: int = 400, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}

async def app_exception_handler(request: Request, exc: AppError):
    # Standard error body:
    # - keeps legacy keys: error_code, message, details
    # - adds top-level detail for UI
    # - if details contains feature/module, also expose them at top-level
    content = {
        "error_code": exc.error_code,
        "message": exc.message,
        "detail": exc.message,
        "details": exc.details,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if exc.status_code == 403:
        content["error_code"] = "FORBIDDEN"

    # Kill Switch contract (P0): module disabled errors MUST return a minimal,
    # deterministic body: {"error":"MODULE_DISABLED","module":"CRM"}
    if exc.error_code == "MODULE_DISABLED":
        mod = None
        if isinstance(exc.details, dict):
            mod = exc.details.get("module")
        if isinstance(mod, str):
            mod = mod.upper()
        else:
            mod = "UNKNOWN"

        return JSONResponse(status_code=exc.status_code, content={"error": "MODULE_DISABLED", "module": mod})

    if isinstance(exc.details, dict):
        for key in ("feature", "module", "tenant_id", "reason"):
            if key in exc.details:
                content[key] = exc.details[key]

    return JSONResponse(status_code=exc.status_code, content=content)

async def generic_exception_handler(request: Request, exc: Exception):
    # In prod: do not leak internal exception details to clients.
    from config import settings

    details = {"error": str(exc)} if settings.debug else {}

    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
