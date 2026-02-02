from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict


_REDACT_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    # NOTE: do not redact key named "password" in logs globally; some events may
    # legitimately use values like method="password". Avoid logging raw credential values.
    "token",
    "secret",
    "api_key",
}


def _redact_value(value: Any) -> Any:
    if value is None:
        return None
    return "[REDACTED]"


def _mask_sensitive(obj: Any) -> Any:
    """Recursively redact common secrets in dict-like payloads."""
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
    """Structured JSON formatter.

    Canonical fields (stable):
    - timestamp, level, message, request_id, tenant_id, path, method, status_code, duration_ms

    Extra fields are allowed but we keep this stable for ops.
    """

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
        }

        # Keep stable "service" and "env" fields if present
        if hasattr(record, "service"):
            data["service"] = getattr(record, "service")
        if hasattr(record, "env"):
            data["env"] = getattr(record, "env")

        # Attach event if present (useful for Kibana/Grafana filters)
        if hasattr(record, "event"):
            data["event"] = getattr(record, "event")

        # Preserve any other structured extras (masked)
        for key, value in record.__dict__.items():
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            if key in data:
                continue
            # Avoid leaking request headers/cookies/etc if someone logs them
            data[key] = _mask_sensitive(value)

        # If logger.exception was used, attach traceback for server-side debugging
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(_mask_sensitive(data), ensure_ascii=False)


def configure_logging(*, level: str, fmt: str) -> None:
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler()

    if (fmt or "plain").lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    root.addHandler(handler)
    root.setLevel(log_level)
