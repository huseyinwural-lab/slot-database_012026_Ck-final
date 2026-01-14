from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError, app_exception_handler


GAMES_PREFIX = "/api/v1/games"


def _is_games_path(request: Request) -> bool:
    try:
        return request.url.path.startswith(GAMES_PREFIX)
    except Exception:
        return False


def _wrap(error_code: str, message: str, status_code: int, details: Optional[Dict[str, Any]] = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": message,
            "details": details or {},
        },
    )


async def games_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Standardize errors ONLY for Games domain.

    Non-negotiable: do not change other domains.

    Special case: framework-level 404 on games routes should become 501 FEATURE_NOT_IMPLEMENTED
    when it looks like a missing route (e.g., /api/v1/games/{id}/toggle).
    """
    if not _is_games_path(request):
        # Non-negotiable: do not touch other domains.
        return await http_exception_handler(request, exc)

    status = exc.status_code

    if status == 401:
        return _wrap("UNAUTHORIZED", "Unauthorized", 401)
    if status == 403:
        return _wrap("FORBIDDEN", "Forbidden", 403)
    if status == 404:
        # Route missing vs resource missing:
        # - Our real "resource missing" cases should raise AppError with GAME_CONFIG_NOT_FOUND.
        # - If we're here, it is likely a framework-level 404 (route not found).
        return _wrap("FEATURE_NOT_IMPLEMENTED", "Feature not implemented", 501, details={"original_status": 404})
    if status == 501:
        return _wrap("FEATURE_NOT_IMPLEMENTED", "Feature not implemented", 501)

    # For any other HTTPException under /games, keep it deterministic but generic.
    return _wrap("UNKNOWN_ERROR", str(exc.detail) if exc.detail else "Error", status)


async def games_validation_exception_handler(request: Request, exc: RequestValidationError):
    if not _is_games_path(request):
        return await request_validation_exception_handler(request, exc)

    return _wrap(
        "VALIDATION_FAILED",
        "Validation failed",
        422,
        details={"errors": exc.errors()},
    )


async def games_app_error_handler(request: Request, exc: AppError):
    """Wrap AppError ONLY for /api/v1/games.* to match the domain contract."""
    if not _is_games_path(request):
        return await app_exception_handler(request, exc)

    return _wrap(exc.error_code, exc.message, exc.status_code, details=exc.details)
