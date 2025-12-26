import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select, func
from app.models.sql_models import Transaction, Player
from app.core.database import get_session
from app.backend.app.services.tenant_policy_enforcement import check_velocity_limit
from app.backend.config import settings

# Mock minimal session context
async def test_velocity():
    print("=== Testing Velocity Engine ===")
    
    # Needs a running DB or mock. Since we are in container with running DB:
    from app.core.database import async_session
    
    async with async_session() as session:
        # Create dummy user if needed or pick one
        # For simplicity, we assume 'test_velocity_user'
        player_id = "test_velocity_user"
        
        print(f"User: {player_id}")
        print(f"Limit: {settings.max_tx_velocity_count} per {settings.max_tx_velocity_window_minutes} min")
        
        # Insert 6 transactions rapidly
        for i in range(6):
            tx = Transaction(
                tenant_id="default",
                player_id=player_id,
                type="deposit",
                amount=10.0,
                status="completed",
                state="completed"
            )
            session.add(tx)
        await session.commit()
        print("Inserted 6 dummy transactions.")
        
        # Now check limit
        try:
            await check_velocity_limit(session, player_id=player_id, action="deposit")
            print("[FAIL] Velocity check did NOT raise exception.")
        except Exception as e:
            if "VELOCITY_LIMIT_EXCEEDED" in str(e) or "429" in str(e):
                print(f"[PASS] Caught expected error: {e}")
            else:
                print(f"[FAIL] Caught unexpected error: {e}")

if __name__ == "__main__":
    # This script is a stub for manual verification if needed
    pass
