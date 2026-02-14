import pytest
from datetime import datetime, timedelta
from app.models.risk import RiskProfile, RiskLevel
import uuid

@pytest.mark.asyncio
async def test_override_with_expiry(client, async_session_factory):
    # Setup Admin & User
    from app.utils.auth import create_access_token
    from app.models.sql_models import Tenant, AdminUser
    
    user_id = str(uuid.uuid4())
    
    async with async_session_factory() as s:
        tenant = Tenant(name="ExpiryTest", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        admin = AdminUser(
            tenant_id=tenant.id,
            username="expiry_admin",
            email="expiry@admin.com",
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
        
        profile = RiskProfile(user_id=user_id, tenant_id=tenant.id, risk_score=10, risk_level=RiskLevel.LOW)
        s.add(profile)
        await s.commit()
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Apply Override with Expiry (24h)
    payload = {"score": 90, "reason": "Short term block", "expiry_hours": 24}
    resp = await client.post(f"/api/v1/admin/risk/{user_id}/override", json=payload, headers=headers)
    
    assert resp.status_code == 200
    
    # Verify DB
    async with async_session_factory() as s:
        profile = await s.get(RiskProfile, user_id)
        assert profile.risk_score == 90
        assert profile.risk_level == RiskLevel.HIGH
        assert profile.override_expires_at is not None
        assert profile.override_expires_at > datetime.utcnow()
        assert profile.flags.get("override_active") is True
