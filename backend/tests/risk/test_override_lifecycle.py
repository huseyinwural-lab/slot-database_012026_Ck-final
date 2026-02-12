import pytest
from datetime import datetime, timedelta
from app.models.risk import RiskProfile, RiskLevel
from app.models.risk_history import RiskHistory
from app.services.risk_service import RiskService

@pytest.mark.asyncio
async def test_override_lifecycle(client, session, async_session_factory):
    from app.utils.auth import create_access_token
    from app.models.sql_models import Tenant, AdminUser
    import uuid
    
    # 1. Setup Admin
    async with async_session_factory() as s:
        tenant = Tenant(name="LifecycleTest", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        admin = AdminUser(
            tenant_id=tenant.id,
            username="lifecycle_admin",
            email="lifecycle@admin.com",
            full_name="Risk Admin",
            password_hash="pw",
            role="Admin",
            tenant_role="operations"
        )
        s.add(admin)
        await s.commit()
        
        token = create_access_token(
            data={"sub": str(admin.id), "email": admin.email, "tenant_id": tenant.id, "role": "Admin"},
            expires_delta=timedelta(minutes=30)
        )
        
        user_id = str(uuid.uuid4())
        profile = RiskProfile(user_id=user_id, tenant_id=tenant.id, risk_score=10, risk_level=RiskLevel.LOW)
        s.add(profile)
        await s.commit()
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Apply Override with Expiry
    # Note: API might not support expiry param yet, but we will add it or verify DB column
    # If API update is pending, we can test service level or update API now.
    # Let's assume we update API to accept expiry_hours
    
    # For now, let's verify manual DB update simulates expiry logic if we were to implement the job.
    # But wait, the task is "Override Governance Strengthening".
    # "Expired override -> otomatik revert job".
    # We should at least verify the column exists and we can set it.
    
    # Let's update the API first to accept expiry.
    pass
