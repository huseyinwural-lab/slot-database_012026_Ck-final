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

    # Kill Switch contract (P0): standardize module disabled errors
    # Required body: {"error":"MODULE_DISABLED","module":"CRM"}
    if exc.error_code == "MODULE_DISABLED":
        content["error"] = "MODULE_DISABLED"

    if isinstance(exc.details, dict):
        for key in ("feature", "module", "tenant_id", "reason"):
            if key in exc.details:
                content[key] = exc.details[key]

    if exc.error_code == "MODULE_DISABLED":
        # Ensure module is exposed at top-level and uppercased (e.g., CRM)
        mod = content.get("module")
        if isinstance(mod, str):
            content["module"] = mod.upper()

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
