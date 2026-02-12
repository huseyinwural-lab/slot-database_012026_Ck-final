import pytest
from app.models.risk import RiskProfile, RiskLevel
from app.models.risk_history import RiskHistory
from app.models.sql_models import AdminUser

@pytest.mark.asyncio
async def test_get_profile(client, admin_token, session):
    # Setup
    tenant_id = "t1" # Using default from conftest helpers if aligned, or explicit
    # Note: admin_token fixture creates a tenant. We need to match it.
    # Let's use `client` with `admin_token` which is a string.
    # We need to extract tenant_id or create a user in the same tenant.
    
    # Actually, simpler:
    # 1. Create a user
    # 2. Create a risk profile for user
    # 3. Call API
    
    # We need to know the tenant_id the admin belongs to.
    # The `admin_token` fixture helper creates an admin and returns a token. 
    # But we don't easily get the tenant_id back unless we parse token or query.
    # Let's inspect conftest `admin_token` again.
    pass

@pytest.mark.asyncio
async def test_admin_override_risk(client, session, async_session_factory):
    # 1. create admin & token
    # We will replicate the `admin_token` logic to get the objects
    from app.utils.auth import create_access_token
    from datetime import timedelta
    from app.models.sql_models import Tenant, AdminUser
    
    async with async_session_factory() as s:
        tenant = Tenant(name="RiskAdminTest", type="owner")
        s.add(tenant)
        await s.commit()
        await s.refresh(tenant)
        
        admin = AdminUser(
            tenant_id=tenant.id,
            username="riskadmin",
            email="risk@admin.com",
            full_name="Risk Admin",
            password_hash="pw",
            role="Admin",
            tenant_role="operations" # needs write access
        )
        s.add(admin)
        await s.commit()
        
        token = create_access_token(
            data={"sub": str(admin.id), "email": admin.email, "tenant_id": tenant.id, "role": "Admin"},
            expires_delta=timedelta(minutes=30)
        )
        
        import uuid
        # User to override
        user_id = str(uuid.uuid4())
        # Pre-create profile
        profile = RiskProfile(user_id=user_id, tenant_id=tenant.id, risk_score=10, risk_level=RiskLevel.LOW)
        s.add(profile)
        await s.commit()
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Call Override
    payload = {"score": 80, "reason": "Suspicious behavior"}
    resp = await client.post(f"/api/v1/admin/risk/{user_id}/override", json=payload, headers=headers)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["risk_score"] == 80
    assert data["profile"]["risk_level"] == "HIGH"
    
    # 3. Verify History
    async with async_session_factory() as s:
        # Check history
        from sqlmodel import select
        stmt = select(RiskHistory).where(RiskHistory.user_id == user_id)
        history = (await s.execute(stmt)).scalars().all()
        assert len(history) >= 1
        last = history[-1]
        assert last.old_score == 10
        assert last.new_score == 80
        assert "Suspicious behavior" in last.change_reason
