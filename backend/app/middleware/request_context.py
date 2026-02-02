from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging

logger = logging.getLogger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # IP
        ip = request.client.host if request.client else "unknown"
        request.state.ip_address = ip
        
        # User Agent
        ua = request.headers.get("User-Agent", "unknown")
        request.state.user_agent = ua
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
