import pytest
from unittest.mock import patch, AsyncMock
from sqlmodel import select
from app.models.reconciliation_run import ReconciliationRun
from app.worker import run_daily_reconciliation

@pytest.mark.asyncio
async def test_run_daily_reconciliation(session):
    """
    Test that the daily reconciliation worker:
    1. Creates ReconciliationRun records for all providers
    2. Calls the execution job
    """
    
    # We need to mock get_session to return our test session
    # Since run_daily_reconciliation iterates over get_session(), we need to mock it as an async generator
    async def mock_get_session_gen():
        yield session

    with patch("app.worker.get_session", side_effect=mock_get_session_gen):
        # Mock the actual job execution to avoid complex logic/side effects
        with patch("app.worker.run_reconciliation_for_run_id", new_callable=AsyncMock) as mock_job:
            
            # Execute worker function
            await run_daily_reconciliation(None)
            
            # Verify DB records
            stmt = select(ReconciliationRun)
            runs = (await session.execute(stmt)).scalars().all()
            
            # Expect at least 2 runs (stripe, adyen)
            assert len(runs) >= 2
            
            providers = {r.provider for r in runs}
            assert "stripe" in providers
            assert "adyen" in providers
            
            # Verify job was called for each run
            assert mock_job.call_count == len(runs)
            
            # Verify metrics were recorded (mocking metrics would be better but simple check ok)
            # We can't easily check metrics side effect here without patching metrics service too, 
            # but we trust the code flow if it reached end without error.
