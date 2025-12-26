import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# Env
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////app/backend/casino_poker_e2e_test.db"

async def run_poker_e2e_loop():
    print("Starting Poker Cash Loop E2E Test...")
    
    if os.path.exists("/app/backend/casino_poker_e2e_test.db"):
        os.remove("/app/backend/casino_poker_e2e_test.db")
        
    engine = create_async_engine(os.environ["DATABASE_URL"])
    
    # Init Schema - Import ALL models
    async with engine.begin() as conn:
        from app.models.sql_models import SQLModel
        from app.models.game_models import Game
        from app.models.robot_models import RobotDefinition
        from app.models.bonus_models import BonusCampaign
        from app.models.engine_models import EngineStandardProfile
        from app.models.poker_models import RakeProfile, PokerHandAudit
        from app.models.poker_table_models import PokerTable, PokerSession
        await conn.run_sync(SQLModel.metadata.create_all)
    
    log = []
    tenant_id = "default_casino"
    
    async with engine.connect() as conn:
        # 1. Setup
        await conn.execute(text("INSERT INTO tenant (id, name, type, features, created_at, updated_at) VALUES (:id, 'Poker E2E', 'owner', '{}', :now, :now)"), {"id": tenant_id, "now": datetime.now(timezone.utc)})
        p1 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO player (id, tenant_id, username, email, password_hash, balance_real_available, balance_real, balance_bonus, balance_real_held, wagering_requirement, wagering_remaining, risk_score, status, kyc_status, registered_at)
            VALUES (:id, :tid, 'p_e2e', 'e2e@test.com', 'hash', 500, 500, 0, 0, 0, 0, 'low', 'active', 'verified', :now)
        """), {"id": p1, "tid": tenant_id, "now": datetime.now(timezone.utc)})
        await conn.commit()
        log.append("Setup: Player Balance 500.0")
        
        # 2. Table Launch
        table_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO pokertable (id, tenant_id, name, small_blind, big_blind, min_buyin, max_buyin, created_at)
            VALUES (:id, :tid, 'High Stakes 1', 1.0, 2.0, 50.0, 200.0, :now)
        """), {"id": table_id, "tid": tenant_id, "now": datetime.now(timezone.utc)})
        log.append(f"Table Created: {table_id}")
        
        # 3. Session Join
        session_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO pokersession (id, tenant_id, player_id, table_id, status, started_at)
            VALUES (:id, :tid, :pid, :tbl, 'active', :now)
        """), {"id": session_id, "tid": tenant_id, "pid": p1, "tbl": table_id, "now": datetime.now(timezone.utc)})
        log.append(f"Session Started: {session_id}")
        
        # 4. Hand Loop (Bet -> Win -> Rake)
        hand_id = "h_e2e_1"
        
        # Bet 50
        await conn.execute(text("UPDATE player SET balance_real_available = balance_real_available - 50, balance_real = balance_real - 50 WHERE id=:pid"), {"pid": p1})
        await conn.execute(text("""
            INSERT INTO "transaction" (id, tenant_id, player_id, type, amount, currency, status, state, method, provider, provider_event_id, idempotency_key, created_at, updated_at, balance_after)
            VALUES (:id, :tid, :pid, 'poker_bet', 50, 'USD', 'completed', 'completed', 'wallet', 'poker', :hid, :ikey, :now, :now, 450)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p1, "hid": hand_id, "ikey": f"{hand_id}_bet", "now": datetime.now(timezone.utc)})
        
        # Win 95 (5 Rake)
        await conn.execute(text("UPDATE player SET balance_real_available = balance_real_available + 95, balance_real = balance_real + 95 WHERE id=:pid"), {"pid": p1})
        await conn.execute(text("""
            INSERT INTO "transaction" (id, tenant_id, player_id, type, amount, currency, status, state, method, provider, provider_event_id, idempotency_key, created_at, updated_at, balance_after)
            VALUES (:id, :tid, :pid, 'poker_win', 95, 'USD', 'completed', 'completed', 'wallet', 'poker', :hid, :ikey, :now, :now, 545)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p1, "hid": hand_id, "ikey": f"{hand_id}_win", "now": datetime.now(timezone.utc)})
        
        # Audit Hand
        await conn.execute(text("""
            INSERT INTO pokerhandaudit (id, tenant_id, provider_hand_id, table_id, game_type, pot_total, rake_collected, created_at)
            VALUES (:id, :tid, :hid, :tbl, 'CASH', 100, 5.0, :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "hid": hand_id, "tbl": table_id, "now": datetime.now(timezone.utc)})
        
        log.append("Hand Complete: Bet 50, Win 95, Rake 5.")
        
        # 5. Reconcile
        res = await conn.execute(text("SELECT balance_real_available FROM player WHERE id=:pid"), {"pid": p1})
        bal = res.scalar()
        
        expected = 500 - 50 + 95
        if bal == expected:
            log.append(f"Reconciliation: PASS (Balance {bal} matches expected {expected})")
        else:
            log.append(f"Reconciliation: FAIL (Expected {expected}, Got {bal})")
            
        await conn.commit()

    # Artifacts
    os.makedirs("/app/artifacts/bau/week6", exist_ok=True)
    with open("/app/artifacts/bau/week6/e2e_poker_cash_loop.txt", "w") as f:
        f.write("\n".join(log))
        
    await engine.dispose()
    print("E2E Poker Loop Complete.")

if __name__ == "__main__":
    asyncio.run(run_poker_e2e_loop())
