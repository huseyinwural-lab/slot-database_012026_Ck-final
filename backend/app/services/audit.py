from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.models.modules import AdminActivityLog
from app.core.database import db_wrapper
from app.models.domain.admin import AdminUser

class AuditLogger:
    @staticmethod
    async def log(
        admin: AdminUser,
        action: str,
        module: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
        ip_address: Optional[str] = None
    ):
        """
        Standardized method to log admin activities.
        """
        db = db_wrapper.db
        
        log_entry = AdminActivityLog(
            admin_id=admin.id,
            admin_name=admin.full_name or admin.email,
            action=action,
            module=module,
            target_entity_id=target_id,
            ip_address=ip_address or "unknown",
            before_snapshot=None, # Can be enriched by caller
            after_snapshot=details,
            risk_level=risk_level,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Fire and forget (async insert)
        await db.admin_activity_log.insert_one(log_entry.model_dump())

audit = AuditLogger()
