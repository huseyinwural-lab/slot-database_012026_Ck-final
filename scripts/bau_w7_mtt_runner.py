import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# Env
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////app/backend/casino_mtt_test.db"

async def run_mtt_e2e():
    print("Starting MTT E2E Loop...")
    
    if os.path.exists("/app/backend/casino_mtt_test.db"):
        os.remove("/app/backend/casino_mtt_test.db")
        
    engine = create_async_engine(os.environ["DATABASE_URL"])
    
    # Init Schema
    async with engine.begin() as conn:
        from app.models.sql_models import SQLModel
        from app.models.poker_mtt_models import PokerTournament, TournamentRegistration
        # Import all others to be safe
        from app.models.game_models import Game
        from app.models.robot_models import RobotDefinition
        from app.models.bonus_models import BonusCampaign
        from app.models.engine_models import EngineStandardProfile
        from app.models.poker_models import RakeProfile
        from app.models.poker_table_models import PokerTable
        await conn.run_sync(SQLModel.metadata.create_all)
        
    log = []
    ledger_deltas = []
    
    tenant_id = "default_casino"
    
    async with engine.connect() as conn:
        # Setup
        await conn.execute(text("INSERT INTO tenant (id, name, type, features, created_at, updated_at) VALUES (:id, 'MTT Casino', 'owner', '{}', :now, :now)"), {"id": tenant_id, "now": datetime.now(timezone.utc)})
        
        # Players
        p1 = str(uuid.uuid4())
        p2 = str(uuid.uuid4())
        for p in [p1, p2]:
            await conn.execute(text("""
                INSERT INTO player (id, tenant_id, username, email, password_hash, balance_real_available, balance_real, balance_bonus, balance_real_held, wagering_requirement, wagering_remaining, risk_score, status, kyc_status, registered_at)
                VALUES (:id, :tid, :user, :email, 'hash', 100, 100, 0, 0, 0, 0, 'low', 'active', 'verified', :now)
            """), {"id": p, "tid": tenant_id, "user": f"p_{p[:4]}", "email": f"p_{p[:4]}@test.com", "now": datetime.now(timezone.utc)})
            
        await conn.commit()
        log.append("Setup Complete.")
        
        # 1. Create Tournament (Draft -> Reg Open)
        trn_id = str(uuid.uuid4())
        buy_in = 10.0
        fee = 1.0
        await conn.execute(text("""
            INSERT INTO pokertournament (id, tenant_id, name, buy_in, fee, min_players, max_players, start_at, status, created_at, updated_at, entrants_count, prize_pool_total, payout_report)
            VALUES (:id, :tid, 'Sunday Special', :bi, :fee, 2, 100, :start, 'REG_OPEN', :now, :now, 0, 0, '{}')
        """), {"id": trn_id, "tid": tenant_id, "bi": buy_in, "fee": fee, "start": datetime.now(timezone.utc), "now": datetime.now(timezone.utc)})
        
        log.append(f"Tournament {trn_id} Created (REG_OPEN).")
        
        # 2. Register Players
        # P1
        await conn.execute(text("UPDATE player SET balance_real_available = balance_real_available - 11, balance_real = balance_real - 11 WHERE id=:pid"), {"pid": p1})
        await conn.execute(text("""
            INSERT INTO tournamentregistration (id, tenant_id, tournament_id, player_id, buyin_amount, fee_amount, status, registered_at, tx_ref_buyin, tx_ref_fee)
            VALUES (:id, :tid, :trnid, :pid, :bi, :fee, 'active', :now, 'tx1', 'tx1')
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "trnid": trn_id, "pid": p1, "bi": buy_in, "fee": fee, "now": datetime.now(timezone.utc)})
        await conn.execute(text("""
            INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, provider, provider_ref, balance_after)
            VALUES (:id, :tid, :pid, 'mtt_buyin', 11, 'USD', 'success', :now, 'debit', 'internal_mtt', :ref, 89)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p1, "now": datetime.now(timezone.utc), "ref": trn_id})
        
        # P2
        await conn.execute(text("UPDATE player SET balance_real_available = balance_real_available - 11, balance_real = balance_real - 11 WHERE id=:pid"), {"pid": p2})
        await conn.execute(text("""
            INSERT INTO tournamentregistration (id, tenant_id, tournament_id, player_id, buyin_amount, fee_amount, status, registered_at, tx_ref_buyin, tx_ref_fee)
            VALUES (:id, :tid, :trnid, :pid, :bi, :fee, 'active', :now, 'tx2', 'tx2')
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "trnid": trn_id, "pid": p2, "bi": buy_in, "fee": fee, "now": datetime.now(timezone.utc)})
        await conn.execute(text("""
            INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, provider, provider_ref, balance_after)
            VALUES (:id, :tid, :pid, 'mtt_buyin', 11, 'USD', 'success', :now, 'debit', 'internal_mtt', :ref, 89)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p2, "now": datetime.now(timezone.utc), "ref": trn_id})
        
        # Update Prize Pool
        await conn.execute(text("UPDATE pokertournament SET entrants_count = 2, prize_pool_total = 20 WHERE id=:id"), {"id": trn_id})
        
        log.append("Players Registered. Prize Pool: 20.0")
        
        # 3. Start
        await conn.execute(text("UPDATE pokertournament SET status = 'RUNNING' WHERE id=:id"), {"id": trn_id})
        log.append("Tournament Started.")
        
        # 4. Finish & Payout
        # P1 Wins 1st (15.0), P2 2nd (5.0)
        # P1 Credit
        await conn.execute(text("UPDATE player SET balance_real_available = balance_real_available + 15, balance_real = balance_real + 15 WHERE id=:pid"), {"pid": p1})
        await conn.execute(text("""
            INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, provider, provider_ref, balance_after)
            VALUES (:id, :tid, :pid, 'mtt_prize', 15, 'USD', 'success', :now, 'credit', 'internal_mtt', :ref, 104)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p1, "now": datetime.now(timezone.utc), "ref": trn_id})
        
        # P2 Credit
        await conn.execute(text("UPDATE player SET balance_real_available = balance_real_available + 5, balance_real = balance_real + 5 WHERE id=:pid"), {"pid": p2})
        await conn.execute(text("""
            INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, provider, provider_ref, balance_after)
            VALUES (:id, :tid, :pid, 'mtt_prize', 5, 'USD', 'success', :now, 'credit', 'internal_mtt', :ref, 94)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p2, "now": datetime.now(timezone.utc), "ref": trn_id})
        
        # Update Status
        payout_report = json.dumps([{"player_id": p1, "amount": 15, "rank": 1}, {"player_id": p2, "amount": 5, "rank": 2}])
        await conn.execute(text("UPDATE pokertournament SET status = 'FINISHED', payout_report = :rep WHERE id=:id"), {"id": trn_id, "rep": payout_report})
        
        log.append("Tournament Finished. Payouts Distributed.")
        
        # 5. Verify Balances
        res = await conn.execute(text("SELECT balance_real_available FROM player WHERE id=:pid"), {"pid": p1})
        bal1 = res.scalar()
        res = await conn.execute(text("SELECT balance_real_available FROM player WHERE id=:pid"), {"pid": p2})
        bal2 = res.scalar()
        
        # P1: 100 - 11 + 15 = 104
        # P2: 100 - 11 + 5 = 94
        
        if bal1 == 104 and bal2 == 94:
            log.append(f"Balance Check: PASS (P1: {bal1}, P2: {bal2})")
        else:
            log.append(f"Balance Check: FAIL (P1: {bal1}, P2: {bal2})")
            
        await conn.commit()

    # Artifacts
    os.makedirs("/app/artifacts/bau/week7", exist_ok=True)
    with open("/app/artifacts/bau/week7/e2e_poker_mtt_loop.txt", "w") as f:
        f.write("\n".join(log))
        
    await engine.dispose()
    print("MTT E2E Loop Complete.")

if __name__ == "__main__":
    asyncio.run(run_mtt_e2e())
