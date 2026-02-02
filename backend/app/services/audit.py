from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from app.models.sql_models import AdminUser, AuditEvent
import hashlib
import json

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
    """P2 Audit logger (Task 4 Enhanced + D1.4 Hash Chaining)."""

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
        
        status: str = "SUCCESS", 
        reason: Optional[str] = None,
        actor_role: Optional[str] = None,
        user_agent: Optional[str] = None,
        
        details: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        diff: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        
        ip_address: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        
        # Ensure timestamp is consistent (strip microseconds to avoid DB roundtrip issues)
        # NOTE: DB column is TIMESTAMP WITHOUT TIME ZONE in Postgres.
        # Use naive UTC datetime to avoid tz-aware insertion errors.
        timestamp = datetime.utcnow().replace(microsecond=0)
        
        # 1. Fetch previous hash for this tenant chain
        stmt = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id).order_by(desc(AuditEvent.sequence)).limit(1)
        prev_event = (await session.execute(stmt)).scalars().first()
        
        prev_row_hash = prev_event.row_hash if prev_event and prev_event.row_hash else "0" * 64
        sequence = (prev_event.sequence + 1) if prev_event and prev_event.sequence is not None else 1
        
        # 2. Canonical JSON for current event
        payload = {
            "tenant_id": tenant_id,
            "actor_user_id": actor_user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "timestamp": timestamp.isoformat(),
            "reason": reason,
            "status": status,
            "details": _mask_sensitive(details or {}),
            "sequence": sequence
        }
        canonical_str = json.dumps(payload, sort_keys=True)
        
        # 3. Compute Hash
        row_hash = hashlib.sha256((prev_row_hash + canonical_str).encode('utf-8')).hexdigest()
        
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
            timestamp=timestamp,
            
            # Chain fields
            chain_id=tenant_id,
            sequence=sequence,
            prev_row_hash=prev_row_hash,
            row_hash=row_hash
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
        reason: Optional[str] = None,
        before: Optional[Dict] = None,
        after: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Backward-compatible wrapper."""

        if not session:
            return

        rid = request_id or "unknown"
        tid = tenant_id or getattr(admin, "tenant_id", "unknown")
        
        status = "SUCCESS"
        if result == "failed":
            status = "FAILED"
        if result == "blocked":
            status = "DENIED"

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
