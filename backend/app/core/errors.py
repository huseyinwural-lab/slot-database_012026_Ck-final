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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
