from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.models.sql_models import AuditLog
from app.core.database import get_session
from app.models.sql_models import AdminUser
from sqlalchemy.ext.asyncio import AsyncSession

class AuditLogger:
    @staticmethod
    async def log(
        admin: AdminUser,
        action: str,
        module: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ):
        """
        Standardized method to log admin activities.
        Requires an active session passed or handles it (if context var available - simplified for now).
        Ideally, pass the session from the route.
        """
        if not session:
            # In a real app, we might contextvars or similar, but here we expect session to be passed
            # or we create a new one (less efficient).
            # For this refactor, we will enforce passing session where possible.
            # If session is missing, we might skip logging or raise warning.
            return

        log_entry = AuditLog(
            admin_id=admin.id,
            action=action,
            module=module,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address or "unknown",
            timestamp=datetime.utcnow()
        )
        
        session.add(log_entry)
        # We don't commit here usually, let the caller commit transaction.
        # But for audit, sometimes we want immediate commit.
        # Let's trust caller transaction scope.

audit = AuditLogger()
