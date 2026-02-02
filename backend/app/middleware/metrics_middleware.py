from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.services.metrics import metrics

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        metrics.increment_request()
        
        try:
            response = await call_next(request)
            
            if 400 <= response.status_code < 500:
                metrics.increment_error_4xx()
            elif response.status_code >= 500:
                metrics.increment_error_5xx()
                
            return response
        except Exception as e:
            metrics.increment_error_5xx()
            raise e
