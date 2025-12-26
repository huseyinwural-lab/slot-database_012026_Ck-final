from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql_models import AdminUser, AuditEvent

_REDACT_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "token",
    "secret",
    "api_key",
    "password"
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
    """P2 Audit logger (Task 4 Enhanced)."""

    @staticmethod
    async def log_event(
        *,
        session: AsyncSession,
        # Mandatory Context
        request_id: str,
        actor_user_id: str,
        tenant_id: str,
        # Action Info
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        result: str, # Kept for compat
        
        # Task 4 New Fields
        status: str = "SUCCESS", # SUCCESS | FAILED | DENIED
        reason: Optional[str] = None,
        actor_role: Optional[str] = None,
        user_agent: Optional[str] = None,
        
        # Data
        details: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        diff: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        
        # Network
        ip_address: Optional[str] = None,
        
        # Error
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        
        evt = AuditEvent(
            request_id=request_id,
            actor_user_id=actor_user_id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            status=status,
            reason=reason,
            actor_role=actor_role,
            ip_address=ip_address,
            user_agent=user_agent,
            details=_mask_sensitive(details or {}),
            before_json=_mask_sensitive(before),
            after_json=_mask_sensitive(after),
            diff_json=_mask_sensitive(diff),
            metadata_json=_mask_sensitive(metadata),
            error_code=error_code,
            error_message=error_message,
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
        # New Task 4 Compat args
        reason: Optional[str] = None,
        before: Optional[Dict] = None,
        after: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Backward-compatible wrapper used by existing routes."""

        if not session:
            return

        rid = request_id or "unknown"
        tid = tenant_id or getattr(admin, "tenant_id", "unknown")
        
        # Map result to status
        status = "SUCCESS"
        if result == "failed": status = "FAILED"
        if result == "blocked": status = "DENIED"

        await AuditLogger.log_event(
            session=session,
            request_id=rid,
            actor_user_id=str(admin.id),
            actor_role=getattr(admin, "role", "unknown"),
            tenant_id=tid,
            action=action,
            resource_type=resource_type or module,
            resource_id=target_id,
            result=result,
            status=status,
            reason=reason,
            details=details,
            ip_address=ip_address,
            before=before,
            after=after,
            metadata=metadata
        )

audit = AuditLogger()
