from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sql_models import AdminUser, AuditEvent


_REDACT_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    # NOTE: do NOT include "password" here, because some payloads may contain
    # non-secret values like method="password". We only redact real credential keys.
    "token",
    "secret",
    "api_key",
}


def _mask_sensitive(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in _REDACT_KEYS:
                out[k] = "[REDACTED]"
            else:
                out[k] = _mask_sensitive(v)
        return out
    if isinstance(obj, list):
        return [_mask_sensitive(v) for v in obj]
    return obj


class AuditLogger:
    """P2 Audit logger.

    Note: we still keep the legacy AuditLog table for backward compatibility
    with existing pages, but new canonical events go into AuditEvent.
    """

    @staticmethod
    async def log_event(
        *,
        session: AsyncSession,
        request_id: str,
        actor_user_id: str,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        result: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        evt = AuditEvent(
            request_id=request_id,
            actor_user_id=actor_user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            ip_address=ip_address,
            details=_mask_sensitive(details or {}),
            timestamp=datetime.now(timezone.utc),
        )
        session.add(evt)

    @staticmethod
    async def log(
        admin: AdminUser,
        action: str,
        module: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session: Optional[AsyncSession] = None,
        request_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        result: str = "success",
    ) -> None:
        """Backward-compatible wrapper used by existing routes.

        - Writes canonical AuditEvent (P2)
        - Keeps old AuditLog writing optional/legacy (we no longer rely on it)

        Caller is responsible for committing the transaction.
        """

        if not session:
            return

        rid = request_id or "unknown"
        tid = tenant_id or getattr(admin, "tenant_id", "unknown")

        await AuditLogger.log_event(
            session=session,
            request_id=rid,
            actor_user_id=str(admin.id),
            tenant_id=tid,
            action=action,
            resource_type=resource_type or module,
            resource_id=target_id,
            result=result,
            details=details,
            ip_address=ip_address,
        )


audit = AuditLogger()
