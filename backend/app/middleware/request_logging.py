import time
import logging
from typing import Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging with correlation ID.

    - Generates/propagates X-Request-ID
    - Logs method, path, status, latency and correlation id
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        start_time = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            logger.exception(
                "request failed",
                extra={
                    "correlation_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = (time.monotonic() - start_time) * 1000.0
        # Echo correlation id back to the client
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "%s %s -> %s in %.1fms [req_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
