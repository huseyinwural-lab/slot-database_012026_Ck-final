from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter.

    Canonical fields (stable):
    - timestamp, level, message, request_id, tenant_id, path, method, status_code, duration_ms

    Extra fields are allowed but we keep this stable for ops.
    """

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
        }

        # If logger.exception was used, attach traceback for server-side debugging
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(data, ensure_ascii=False)


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
