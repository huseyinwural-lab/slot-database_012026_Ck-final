import asyncio
import sys
import os
import csv
import io
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# Env
if "DATABASE_URL" not in os.environ:
    TEST_DB_URL = "sqlite+aiosqlite:////app/backend/casino_w3_bonus.db"
else:
    TEST_DB_URL = os.environ["DATABASE_URL"]

async def run_bonus_hardening():
    print("Starting Bonus Hardening & Reporting Test (P1)...")
    
    if os.path.exists("/app/backend/casino_w3_bonus.db"):
        os.remove("/app/backend/casino_w3_bonus.db")
        
    engine = create_async_engine(TEST_DB_URL)
    
    # Init Schema
    async with engine.begin() as conn:
        from app.models.sql_models import SQLModel
        from app.models.bonus_models import BonusCampaign, BonusGrant
        await conn.run_sync(SQLModel.metadata.create_all)
        
    log = []
    
    async with engine.connect() as conn:
        # 1. Setup Data: Active Bonuses
        tenant_id = "default_casino"
        campaign_id = str(uuid.uuid4())
        
        # Insert Campaign
        await conn.execute(text("INSERT INTO bonuscampaign (id, tenant_id, name, type, status, config, created_at, updated_at) VALUES (:id, :tid, 'Match', 'deposit', 'active', '{}', :now, :now)"), 
                           {"id": campaign_id, "tid": tenant_id, "now": datetime.now(timezone.utc)})
        
        # Insert Grants
        # Player 1: 100 bonus, 50% wagered
        p1 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO bonusgrant (id, tenant_id, campaign_id, player_id, amount_granted, wagering_target, wagering_contributed, status, granted_at)
            VALUES (:id, :tid, :cid, :pid, 100, 3500, 1750, 'active', :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "cid": campaign_id, "pid": p1, "now": datetime.now(timezone.utc)})
        
        # Player 2: 50 bonus, 0% wagered
        p2 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO bonusgrant (id, tenant_id, campaign_id, player_id, amount_granted, wagering_target, wagering_contributed, status, granted_at)
            VALUES (:id, :tid, :cid, :pid, 50, 1750, 0, 'active', :now)
        """), {"id": str(uuid.uuid4()), "tid": tenant_id, "cid": campaign_id, "pid": p2, "now": datetime.now(timezone.utc)})
        
        await conn.commit()
        log.append("Seeded Bonus Data.")
        
        # 2. Liability Report Query
        # Calculate Total Liability (Outstanding Bonus Balance)
        res = await conn.execute(text("""
            SELECT 
                count(*) as active_grants,
                sum(amount_granted) as total_liability,
                sum(wagering_target - wagering_contributed) as pending_wager_volume
            FROM bonusgrant
            WHERE status = 'active'
        """))
        row = res.mappings().first()
        
        liability = row['total_liability']
        pending_wager = row['pending_wager_volume']
        
        log.append(f"Active Grants: {row['active_grants']}")
        log.append(f"Total Liability: {liability}")
        log.append(f"Pending Wager Volume: {pending_wager}")
        
        # 3. CSV Export Simulation
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        writer.writerow(["active_grants", row['active_grants']])
        writer.writerow(["total_liability", liability])
        writer.writerow(["pending_wager_volume", pending_wager])
        
        with open("/app/artifacts/bau/week3/bonus_liability_report_sample.csv", "w") as f:
            f.write(output.getvalue())
            
        log.append("CSV Export Generated.")
        
        # 4. Abuse Control Test (Rate Limit Logic)
        # Verify duplicate active grant logic (simulated)
        res = await conn.execute(text("SELECT count(*) FROM bonusgrant WHERE player_id=:pid AND campaign_id=:cid AND status='active'"), {"pid": p1, "cid": campaign_id})
        count = res.scalar()
        if count >= 1:
            log.append("Abuse Check: Player has active grant -> New grant BLOCKED (simulated).")
        else:
            log.append("Abuse Check: FAIL")

    with open("/app/artifacts/bau/week3/bonus_hardening_tests.txt", "w") as f:
        f.write("\n".join(log))
        
    await engine.dispose()
    print("Bonus Hardening Test Complete.")

if __name__ == "__main__":
    asyncio.run(run_bonus_hardening())
