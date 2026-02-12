import pytest
from app.models.risk import RiskProfile, RiskLevel
from app.models.sql_models import Player

@pytest.mark.asyncio
async def test_withdrawal_blocked_for_high_risk(client, player_with_token, session):
    tenant, player, token = player_with_token
    
    # 1. Manually escalate risk
    # Insert or update risk profile
    profile = RiskProfile(
        user_id=player.id, 
        tenant_id=tenant.id, 
        risk_score=80, 
        risk_level=RiskLevel.HIGH
    )
    session.add(profile)
    await session.commit()
    
    # 2. Fund the player (to bypass insufficient funds)
    player.balance_real_available = 1000.0
    session.add(player)
    await session.commit()
    
    # 3. Attempt Withdrawal
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "risk_test_1"
    }
    payload = {
        "amount": 100.0,
        "method": "crypto",
        "address": "0x123"
    }
    
    resp = await client.post("/api/v1/player/wallet/withdraw", json=payload, headers=headers)
    
    # 4. Verify Block
    assert resp.status_code == 403
    data = resp.json()
    assert data["detail"]["error_code"] == "RISK_BLOCK"

@pytest.mark.asyncio
async def test_withdrawal_allowed_for_low_risk(client, player_with_token, session):
    tenant, player, token = player_with_token
    
    # 1. Low Risk Profile
    profile = RiskProfile(
        user_id=player.id, 
        tenant_id=tenant.id, 
        risk_score=10, 
        risk_level=RiskLevel.LOW
    )
    session.add(profile)
    
    # 2. Fund
    player.balance_real_available = 1000.0
    session.add(player)
    await session.commit()
    
    # 3. Attempt Withdrawal
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "risk_test_2"
    }
    payload = {
        "amount": 100.0,
        "method": "crypto",
        "address": "0x123"
    }
    
    resp = await client.post("/api/v1/player/wallet/withdraw", json=payload, headers=headers)
    
    # 4. Verify Success
    assert resp.status_code == 200
    data = resp.json()
    assert data["transaction"]["state"] == "requested"
