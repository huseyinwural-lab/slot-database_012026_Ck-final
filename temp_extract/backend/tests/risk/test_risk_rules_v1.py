import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.risk_service import RiskService
from app.models.risk import RiskProfile, RiskLevel

@pytest.mark.asyncio
async def test_risk_scoring_logic():
    # Mock DB
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: RiskProfile(user_id="u1", tenant_id="t1", risk_score=10))))
    
    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.pipeline = MagicMock(return_value=MagicMock(execute=AsyncMock()))
    mock_redis.get = AsyncMock(return_value="5") # Simulate velocity count > 3
    
    service = RiskService(mock_db, mock_redis)
    
    # Act: Process Deposit Event (triggering Rapid Deposit rule)
    await service.process_event("DEPOSIT_REQUESTED", "u1", "t1", {"amount": 100})
    
    # Assert
    # Verify DB add called (score updated)
    assert mock_db.add.called
    updated_profile = mock_db.add.call_args[0][0]
    # Base 10 + 30 (Rapid Deposit) = 40
    assert updated_profile.risk_score >= 40 
    assert updated_profile.risk_level == RiskLevel.MEDIUM

@pytest.mark.asyncio
async def test_evaluate_withdrawal_allow():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: RiskProfile(user_id="u1", tenant_id="t1", risk_score=20)))) # Low Score
    
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value="1000") # Low amount
    
    service = RiskService(mock_db, mock_redis)
    
    verdict = await service.evaluate_withdrawal("u1", 50.0)
    assert verdict == "ALLOW"

@pytest.mark.asyncio
async def test_evaluate_withdrawal_block():
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(first=lambda: RiskProfile(user_id="u1", tenant_id="t1", risk_score=80)))) # High Score
    
    mock_redis = MagicMock()
    
    service = RiskService(mock_db, mock_redis)
    
    verdict = await service.evaluate_withdrawal("u1", 50.0)
    assert verdict == "BLOCK"
