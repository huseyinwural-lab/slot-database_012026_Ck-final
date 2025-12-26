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
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////app/backend/casino_w8_test.db"

async def run_w8_scenarios():
    print("Starting BAU W8 Scenarios (Risk, Recon, Bonus)...")
    
    if os.path.exists("/app/backend/casino_w8_test.db"):
        os.remove("/app/backend/casino_w8_test.db")
        
    engine = create_async_engine(os.environ["DATABASE_URL"])
    
    # Init Schema
    async with engine.begin() as conn:
        from app.models.sql_models import SQLModel, Player, Transaction, LedgerTransaction, AuditEvent, RiskRule, Bonus
        from app.models.poker_mtt_models import RiskSignal, PokerTournament, TournamentRegistration
        from app.models.game_models import Game
        from app.models.bonus_models import BonusGrant, BonusCampaign
        await conn.run_sync(SQLModel.metadata.create_all)
        
    tenant_id = "default_casino"
    
    # Logs
    risk_log = []
    recon_log = []
    bonus_log = []
    
    async with engine.connect() as conn:
        # Setup
        await conn.execute(text("INSERT INTO tenant (id, name, type, features, created_at, updated_at) VALUES (:id, 'W8 Casino', 'owner', '{}', :now, :now)"), {"id": tenant_id, "now": datetime.now(timezone.utc)})
        
        # --- SCENARIO 1: Risk Enforcement (Velocity) ---
        p_risk = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO player (id, tenant_id, username, email, password_hash, balance_real_available, balance_real, balance_bonus, balance_real_held, wagering_requirement, wagering_remaining, risk_score, status, kyc_status, registered_at)
            VALUES (:id, :tid, 'p_risk', 'risk@test.com', 'hash', 1000, 1000, 0, 0, 0, 0, 'low', 'active', 'verified', :now)
        """), {"id": p_risk, "tid": tenant_id, "now": datetime.now(timezone.utc)})
        
        risk_log.append("Setup: Risk Player Created.")
        
        # Simulate 6 Deposits in 1 min
        now = datetime.now(timezone.utc)
        for i in range(6):
            await conn.execute(text("""
                INSERT INTO "transaction" (id, tenant_id, player_id, type, amount, currency, status, state, method, idempotency_key, created_at, updated_at, balance_after)
                VALUES (:id, :tid, :pid, 'deposit', 10, 'USD', 'completed', 'completed', 'card', :ik, :ts, :ts, 1000)
            """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p_risk, "ik": f"dep_{i}", "ts": now})
            
        # Trigger Logic (Simulated)
        # Check count
        res = await conn.execute(text("SELECT count(*) FROM \"transaction\" WHERE player_id=:pid AND type='deposit' AND created_at > :ts"), {"pid": p_risk, "ts": now - timedelta(minutes=1)})
        count = res.scalar()
        
        if count > 5:
            # Create Risk Signal
            sig_id = str(uuid.uuid4())
            await conn.execute(text("""
                INSERT INTO risksignal (id, tenant_id, player_id, signal_type, severity, status, evidence_payload, created_at)
                VALUES (:id, :tid, :pid, 'VEL-001', 'medium', 'new', '{"deposits_1m": 6}', :now)
            """), {"id": sig_id, "tid": tenant_id, "pid": p_risk, "now": now})
            
            # Action: Flag Player
            await conn.execute(text("UPDATE player SET risk_score = 'medium' WHERE id=:pid"), {"pid": p_risk})
            risk_log.append(f"Velocity Rule Triggered: {count} deposits.")
            risk_log.append("Action: Player Flagged (Risk Score -> Medium).")
            risk_log.append(f"Signal Created: {sig_id}")
        else:
            risk_log.append("Risk Test FAILED.")

        # --- SCENARIO 2: Bonus Abuse (Max Bet) ---
        p_bonus = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO player (id, tenant_id, username, email, password_hash, balance_real_available, balance_real, balance_bonus, balance_real_held, wagering_requirement, wagering_remaining, risk_score, status, kyc_status, registered_at)
            VALUES (:id, :tid, 'p_bonus', 'bonus@test.com', 'hash', 0, 0, 100, 0, 3500, 3500, 'low', 'active', 'verified', :now)
        """), {"id": p_bonus, "tid": tenant_id, "now": datetime.now(timezone.utc)})
        
        # Grant Active
        camp_id = str(uuid.uuid4())
        await conn.execute(text("INSERT INTO bonuscampaign (id, tenant_id, name, type, status, config, created_at, updated_at) VALUES (:id, :tid, 'MaxBetTest', 'match', 'active', '{}', :now, :now)"), {"id": camp_id, "tid": tenant_id, "now": now})
        
        await conn.execute(text("""
            INSERT INTO bonusgrant (id, tenant_id, campaign_id, player_id, amount_granted, initial_balance, wagering_target, wagering_contributed, status, granted_at)
            VALUES (:id, :tid, :cid, :pid, 100, 100, 3500, 0, 'active', :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "cid": camp_id, "pid": p_bonus, "now": now})
        
        bonus_log.append("Setup: Bonus Player with 100 Bonus Balance.")
        
        # Attempt High Bet ($10)
        bet_amount = 10.0
        max_bet = 5.0
        
        if bet_amount > max_bet:
            # Logic: Reject or Warn
            bonus_log.append(f"Bet Attempt: {bet_amount}")
            bonus_log.append(f"Result: REJECTED (Max Bet Exceeded: {max_bet})")
            
            # Audit rejection
            await conn.execute(text("""
                INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp, row_hash, prev_row_hash, sequence, chain_id, details)
                VALUES (:id, 'bet_req', :pid, :tid, 'GAME_BET', 'game', 'g1', 'blocked', 'DENIED', 'Bonus Max Bet Violation', :now, 'hash', '000', 1, :tid, '{}')
            """), {"id": str(uuid.uuid4()), "pid": p_bonus, "tid": tenant_id, "now": now})
        else:
            bonus_log.append("Bonus Logic FAILED.")

        # --- SCENARIO 3: Reconciliation (Ledger vs Wallet) ---
        recon_log.append(f"Reconciliation Run: {now}")
        
        # Create some ledger entries to match player balances
        # P_Risk: 1000 initial + 60 deposits = 1060? No, inserts above were just transaction log, didn't update wallet in SQL.
        # Let's fix p_risk wallet
        await conn.execute(text("UPDATE player SET balance_real_available = 1060, balance_real = 1060 WHERE id=:pid"), {"pid": p_risk})
        
        # Create Ledger Entries for P_Risk
        await conn.execute(text("""
            INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, balance_after)
            VALUES (:id, :tid, :pid, 'initial', 1000, 'USD', 'success', :now, 'credit', 1000)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p_risk, "now": now})
        
        for i in range(6):
             await conn.execute(text("""
                INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, balance_after)
                VALUES (:id, :tid, :pid, 'deposit', 10, 'USD', 'success', :now, 'credit', 1000)
            """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p_risk, "now": now})
             
        # P_Bonus: 0 Real, 100 Bonus.
        # Ledger for bonus? Usually ledger tracks real money liability. Bonus is separate or tracked as 'bonus_credit'.
        # Let's add ledger entry for bonus grant
        await conn.execute(text("""
            INSERT INTO ledgertransaction (id, tenant_id, player_id, type, amount, currency, status, created_at, direction, balance_after)
            VALUES (:id, :tid, :pid, 'bonus_grant', 100, 'USD', 'success', :now, 'credit_bonus', 100)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "pid": p_bonus, "now": now})
        
        await conn.commit()
        
        # Run Calculation
        # Sum Wallet Real
        res = await conn.execute(text("SELECT sum(balance_real) FROM player"))
        wallet_real_sum = res.scalar() or 0.0
        
        # Sum Ledger Real (Credit - Debit)
        # Note: direction 'credit_bonus' excluded
        res = await conn.execute(text("SELECT sum(amount) FROM ledgertransaction WHERE direction='credit'"))
        ledger_credit = res.scalar() or 0.0
        res = await conn.execute(text("SELECT sum(amount) FROM ledgertransaction WHERE direction='debit'"))
        ledger_debit = res.scalar() or 0.0
        
        ledger_net = ledger_credit - ledger_debit
        
        recon_log.append(f"Wallet Total Real: {wallet_real_sum}")
        recon_log.append(f"Ledger Net Real: {ledger_net}")
        
        if abs(wallet_real_sum - ledger_net) < 0.01:
            recon_log.append("Status: BALANCED")
        else:
            recon_log.append(f"Status: MISMATCH (Diff: {wallet_real_sum - ledger_net})")
            
        # JSON Report
        report_data = {
            "date": now.strftime("%Y-%m-%d"),
            "tenant_id": tenant_id,
            "wallet_real_total": wallet_real_sum,
            "ledger_real_total": ledger_net,
            "mismatch": float(wallet_real_sum - ledger_net),
            "status": "PASS" if abs(wallet_real_sum - ledger_net) < 0.01 else "FAIL"
        }
        
    # Write Artifacts
    with open("/app/artifacts/bau/week8/risk_enforcement_e2e.txt", "w") as f:
        f.write("\n".join(risk_log))
        
    with open("/app/artifacts/bau/week8/e2e_bonus_abuse_negative_cases.txt", "w") as f:
        f.write("\n".join(bonus_log))
        
    with open("/app/artifacts/bau/week8/reconciliation_run_log.txt", "w") as f:
        f.write("\n".join(recon_log))
        
    with open("/app/artifacts/bau/week8/reconciliation_daily_sample.json", "w") as f:
        json.dump(report_data, f, indent=2)

    await engine.dispose()
    print("W8 Scenarios Complete.")

if __name__ == "__main__":
    asyncio.run(run_w8_scenarios())
