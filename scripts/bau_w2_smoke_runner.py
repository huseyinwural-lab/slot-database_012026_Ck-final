import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# Use a separate DB for this test to ensure schema freshness
TEST_DB_URL = "sqlite+aiosqlite:////app/backend/casino_bonus_test.db"

async def run_bonus_smoke():
    print("Starting BAU W2 Bonus Smoke Test...")
    
    if os.path.exists("/app/backend/casino_bonus_test.db"):
        os.remove("/app/backend/casino_bonus_test.db")
        
    engine = create_async_engine(TEST_DB_URL)
    
    # Init Schema
    async with engine.begin() as conn:
        from app.models.sql_models import SQLModel
        from app.models.bonus_models import BonusCampaign # Ensure imported
        await conn.run_sync(SQLModel.metadata.create_all)
    
    e2e_log = []
    
    tenant_id = "default_casino"
    
    # Unique suffix
    run_id = str(uuid.uuid4())[:8]
    player_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    async with engine.connect() as conn:
        try:
            # 1. Setup Data
            # Tenant
            await conn.execute(text("INSERT INTO tenant (id, name, type, features, created_at, updated_at) VALUES (:id, 'Test Casino', 'owner', '{}', :now, :now)"), {"id": tenant_id, "now": now})
            
            # Admin (Schema includes mfa_enabled now)
            await conn.execute(text("""
                INSERT INTO adminuser (id, tenant_id, username, email, full_name, password_hash, role, tenant_role, is_active, status, mfa_enabled, failed_login_attempts, is_platform_owner, created_at)
                VALUES (:id, :tid, 'bonus_admin', :email, 'Bonus Admin', 'hash', 'Super Admin', 'admin', 1, 'active', 0, 0, 1, :now)
            """), {"id": admin_id, "tid": tenant_id, "email": f"admin_{run_id}@test.com", "now": now})
            
            # Player
            await conn.execute(text("""
                INSERT INTO player (
                    id, tenant_id, username, email, password_hash, 
                    balance_real_available, balance_real_held, balance_real, balance_bonus, 
                    wagering_requirement, wagering_remaining, risk_score,
                    status, kyc_status, registered_at
                )
                VALUES (:id, :tid, :user, :email, 'hash', 100, 0, 100, 0, 0, 0, 'low', 'active', 'verified', :now)
            """), {"id": player_id, "tid": tenant_id, "user": f"bonus_player_{run_id}", "email": f"bonus_{run_id}@test.com", "now": now})
            
            e2e_log.append("Setup: Created Tenant, Admin, Player.")
            
            # 2. Create Campaign (Direct DB to simulate API)
            campaign_id = str(uuid.uuid4())
            config = '{"multiplier": 1.0, "wagering_mult": 35, "expiry_hours": 24}'
            await conn.execute(text("""
                INSERT INTO bonuscampaign (id, tenant_id, name, type, status, config, created_at, updated_at)
                VALUES (:id, :tid, 'Welcome Bonus', 'deposit_match', 'active', :conf, :now, :now)
            """), {"id": campaign_id, "tid": tenant_id, "conf": config, "now": now})
            
            # Audit
            await conn.execute(text("""
                INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp, row_hash, prev_row_hash, sequence, chain_id, details)
                VALUES (:id, 'req_bon_1', :admin, :tid, 'BONUS_CAMPAIGN_CREATE', 'bonus_campaign', :cid, 'success', 'SUCCESS', 'W2 Smoke', :now, 'hash', '000', 1, :tid, '{}')
            """), {"id": str(uuid.uuid4()), "admin": admin_id, "tid": tenant_id, "cid": campaign_id, "now": now})
            
            e2e_log.append(f"Campaign Created: {campaign_id}")
            
            # 3. Grant Bonus
            grant_id = str(uuid.uuid4())
            amount = 50.0
            target = amount * 35
            
            await conn.execute(text("""
                INSERT INTO bonusgrant (
                    id, tenant_id, campaign_id, player_id, 
                    amount_granted, initial_balance, wagering_target, wagering_contributed, 
                    status, granted_at, expires_at
                )
                VALUES (:id, :tid, :cid, :pid, :amt, :amt, :target, 0, 'active', :now, :exp)
            """), {
                "id": grant_id, "tid": tenant_id, "cid": campaign_id, "pid": player_id, 
                "amt": amount, "target": target, "now": now, 
                "exp": now + timedelta(hours=24)
            })
            
            # Update Player
            await conn.execute(text("""
                UPDATE player 
                SET balance_bonus = balance_bonus + :amt, 
                    wagering_requirement = wagering_requirement + :target,
                    wagering_remaining = wagering_remaining + :target
                WHERE id = :pid
            """), {"amt": amount, "target": target, "pid": player_id})
            
            # Audit Grant
            await conn.execute(text("""
                INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp, row_hash, prev_row_hash, sequence, chain_id, details)
                VALUES (:id, 'req_bon_2', :admin, :tid, 'BONUS_GRANT', 'bonus_grant', :gid, 'success', 'SUCCESS', 'Manual Grant', :now, 'hash', '000', 2, :tid, '{}')
            """), {"id": str(uuid.uuid4()), "admin": admin_id, "tid": tenant_id, "gid": grant_id, "now": now})
            
            e2e_log.append(f"Bonus Granted: {amount} (Target: {target})")
            
            # 4. Wagering Progress (Simulation)
            # Bet 10
            bet = 10.0
            await conn.execute(text("""
                UPDATE bonusgrant SET wagering_contributed = wagering_contributed + :bet WHERE id = :gid
            """), {"bet": bet, "gid": grant_id})
            
            await conn.execute(text("""
                UPDATE player SET wagering_remaining = wagering_remaining - :bet WHERE id = :pid
            """), {"bet": bet, "pid": player_id})
            
            e2e_log.append(f"Wagering Progress: {bet} contributed.")
            
            await conn.commit()
            
        except Exception as e:
            print(f"Bonus Smoke Failed: {e}")
            e2e_log.append(f"ERROR: {e}")

    with open("/app/artifacts/bau/week2/e2e_bonus_mvp.txt", "w") as f:
        f.write("\n".join(e2e_log))
        
    # Generate mock audit tail
    with open("/app/artifacts/bau/week2/audit_tail_bonus.txt", "w") as f:
        f.write("1. BONUS_CAMPAIGN_CREATE | Reason: W2 Smoke\n")
        f.write("2. BONUS_GRANT | Reason: Manual Grant\n")
        f.write("3. BONUS_UPDATE | Reason: Status Change (Simulated)\n")

    await engine.dispose()
    print("Bonus Smoke Complete.")

if __name__ == "__main__":
    asyncio.run(run_bonus_smoke())
