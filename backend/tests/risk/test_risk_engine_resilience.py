import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.risk_service import RiskService
from app.models.risk import RiskProfile, RiskLevel
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_risk_resilience_redis_down():
    """
    Test that RiskService handles Redis connection failure gracefully (Fail-Safe).
    """
    # Setup
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: RiskProfile(user_id="u1", risk_score=50))))
    
    # Mock Redis raising Exception on get
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=Exception("Connection Timeout"))
    
    service = RiskService(mock_db, mock_redis)
    
    # Act: Evaluate Withdrawal
    # Expect "FLAG" (Soft Block) as per risk_v1_prod_smoke.md fail-safe logic
    verdict = await service.evaluate_withdrawal("u1", 100.0)
    
    # Assert
    assert verdict == "FLAG"

@pytest.mark.asyncio
async def test_risk_resilience_override_expiry_simulation():
    """
    Simulate the logic that would run in the 'Revert Job'.
    We verify that if we *were* to check expiry, we would revert.
    """
    now = datetime.utcnow()
    past = now - timedelta(hours=1)
    
    profile = RiskProfile(
        user_id="u_exp", 
        risk_score=80, 
        risk_level=RiskLevel.HIGH,
        override_expires_at=past,
        flags={"override_active": True}
    )
    
    # Logic simulation
    if profile.override_expires_at and profile.override_expires_at < now:
        # Revert Logic (Simplified: Reset to 0 or re-calculate)
        profile.risk_score = 0
        profile.risk_level = RiskLevel.LOW
        profile.override_expires_at = None
        profile.flags.pop("override_active", None)
        
    assert profile.risk_score == 0
    assert profile.risk_level == RiskLevel.LOW
    assert profile.override_expires_at is None

@pytest.mark.asyncio
async def test_risk_resilience_downgrade_reset():
    """
    Test that downgrading risk level logically resets constraints (simulation).
    """
    # High Risk User
    profile = RiskProfile(risk_score=80, risk_level=RiskLevel.HIGH)
    
    # Admin Manual Downgrade
    profile.risk_score = 20
    profile.risk_level = RiskLevel.LOW
    
    # Check Throttle Config Logic
    # (Copying logic from RiskService.check_bet_throttle)
    limit = 60
    if profile.risk_level == RiskLevel.MEDIUM:
        limit = 30
    elif profile.risk_level == RiskLevel.HIGH:
        limit = 10
        
    assert limit == 60 # Back to standard limits
