import time
import logging
import re
from typing import Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("app.request")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging with correlation ID.

    - Generates/propagates X-Request-ID
    - Logs method, path, status, latency and correlation id
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        incoming_request_id = request.headers.get("X-Request-ID")
        if incoming_request_id and _REQUEST_ID_RE.match(incoming_request_id):
            request_id = incoming_request_id
        else:
            request_id = str(uuid4())

        # Store for downstream access (other middleware / endpoints)
        request.state.request_id = request_id

        start_time = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            tenant_id = request.headers.get("X-Tenant-ID")
            logger.exception(
                "request failed",
                extra={
                    "request_id": request_id,
                    "tenant_id": tenant_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = (time.monotonic() - start_time) * 1000.0
        # Echo correlation id back to the client
        response.headers["X-Request-ID"] = request_id

        tenant_id = request.headers.get("X-Tenant-ID")

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "tenant_id": tenant_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
