import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import asyncio
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
from app.core.database import engine

# Import all models to ensure SQLModel registry is populated correctly
from app.models import (
    sql_models, game_models, robot_models, growth_models, bonus_models, reconciliation,
    engine_models, payment_models, poker_models, poker_mtt_models, poker_table_models,
    rg_models, payment_analytics_models, reconciliation_run, sql_models_extended, vip_models,
    offer_models, dispute_models
)
from app.repositories import ledger_repo

# AuditEvent is likely in sql_models
from app.models.sql_models import AuditEvent

ARCHIVE_DIR = "/app/artifacts/bau/week18/audit_archive"
RETENTION_DAYS = 90

async def archive_audit_logs():
    print("-> Running Audit Archiver...")
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # Threshold (Simulated as 1 day for testing, usually 90)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1) 
    
    async with AsyncSession(engine) as session:
        # 1. Select Old Logs
        stmt = select(AuditEvent).where(AuditEvent.timestamp < cutoff).limit(1000)
        logs = (await session.execute(stmt)).scalars().all()
        
        if not logs:
            print("   No logs to archive.")
            return
            
        print(f"   Found {len(logs)} logs to archive.")
        
        # 2. Write to File (JSONL)
        filename = f"{ARCHIVE_DIR}/audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with open(filename, "w") as f:
            for log in logs:
                # Manual dict conversion for SQLModel
                data = log.model_dump(mode='json')
                f.write(json.dumps(data) + "\n")
        
        print(f"   Archived to: {filename}")
        
        # 3. Delete from DB (Batch)
        ids = [log.id for log in logs]
        del_stmt = delete(AuditEvent).where(AuditEvent.id.in_(ids))
        await session.execute(del_stmt)
        await session.commit()
        print("   Deleted from DB.")

if __name__ == "__main__":
    asyncio.run(archive_audit_logs())
