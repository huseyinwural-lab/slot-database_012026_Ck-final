from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict
from app.core.context import get_log_context

_REDACT_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "token",
    "secret",
    "api_key",
    "password"
}

def _redact_value(value: Any) -> Any:
    if value is None:
        return None
    return "[REDACTED]"

def _mask_sensitive(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in _REDACT_KEYS:
                out[k] = _redact_value(v)
            else:
                out[k] = _mask_sensitive(v)
        return out
    if isinstance(obj, list):
        return [_mask_sensitive(v) for v in obj]
    return obj

class JSONFormatter(logging.Formatter):
    """Structured JSON formatter with Context support."""

    def format(self, record: logging.LogRecord) -> str:
        # Base fields
        data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Merge ContextVars (Global Request Context)
        context_data = get_log_context()
        if context_data:
            data.update(context_data)

        # Merge Record Extras (Local Log Context)
        if hasattr(record, "request_id"): data["request_id"] = record.request_id
        if hasattr(record, "tenant_id"): data["tenant_id"] = record.tenant_id
        
        # Exception Info
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(_mask_sensitive(data), ensure_ascii=False)

def configure_logging(*, level: str, fmt: str) -> None:
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    
    # Force JSON in Prod/Staging, allow plain in Dev if requested
    # But for "Structured Logging" phase, we prefer JSON default.
    if (fmt or "json").lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    root.addHandler(handler)
    root.setLevel(log_level)
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").disabled = True # We use our own middleware
