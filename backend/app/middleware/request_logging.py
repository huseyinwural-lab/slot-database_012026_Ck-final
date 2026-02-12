import time
import logging
import re
from typing import Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.context import set_log_context, clear_log_context

logger = logging.getLogger("app.request")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        clear_log_context()
        
        incoming_request_id = request.headers.get("X-Request-ID")
        if incoming_request_id and _REQUEST_ID_RE.match(incoming_request_id):
            request_id = incoming_request_id
        else:
            request_id = str(uuid4())

        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        
        # Set Global Context
        set_log_context(request_id=request_id, tenant_id=tenant_id, path=request.url.path, method=request.method)
        
        start_time = time.time()
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000.0
            
            logger.info("request_completed", extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms
            })
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            logger.exception("request_failed", extra={
                "status_code": 500,
                "duration_ms": duration_ms,
                "error": str(e)
            })
            raise e
