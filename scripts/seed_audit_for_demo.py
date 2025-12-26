import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings
import json
import hashlib

DATABASE_URL = settings.database_url

async def seed_audit():
    print(f"Seeding audit data to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    
    # Target date: Yesterday (to match export default)
    target_date = datetime.now(timezone.utc) - timedelta(days=1)
    base_time = target_date.replace(hour=10, minute=0, second=0, microsecond=0)
    
    events = []
    prev_hash = "0" * 64
    sequence = 1
    tenant_id = "default_casino"
    
    # Get last sequence if exists? No, we just append for demo. 
    # Actually, if we want verify to pass, we must respect the chain if data exists.
    # But let's assume empty or valid.
    
    async with engine.connect() as conn:
        # Get last
        res = await conn.execute(text("SELECT row_hash, sequence FROM auditevent WHERE tenant_id = :t ORDER BY sequence DESC LIMIT 1"), {"t": tenant_id})
        last = res.mappings().first()
        if last:
            prev_hash = last['row_hash']
            sequence = last['sequence'] + 1
            
        for i in range(5):
            ts = base_time + timedelta(minutes=i)
            ts_str = ts.isoformat()
            
            payload = {
                "tenant_id": tenant_id,
                "actor_user_id": f"admin_{i}",
                "action": "DEMO_ACTION",
                "resource_type": "demo",
                "resource_id": f"res_{i}",
                "timestamp": ts_str,
                "reason": "Demo Seed",
                "status": "SUCCESS",
                "details": {},
                "sequence": sequence
            }
            canonical_str = json.dumps(payload, sort_keys=True)
            row_hash = hashlib.sha256((prev_hash + canonical_str).encode('utf-8')).hexdigest()
            
            # Insert
            await conn.execute(text("""
                INSERT INTO auditevent 
                (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp, details, sequence, prev_row_hash, row_hash)
                VALUES 
                (:id, :rid, :actor, :tid, :act, :res_type, :res_id, :res, :stat, :reason, :ts, :det, :seq, :prev, :hash)
            """), {
                "id": str(uuid.uuid4()),
                "rid": f"req_{i}",
                "actor": f"admin_{i}",
                "tid": tenant_id,
                "act": "DEMO_ACTION",
                "res_type": "demo",
                "res_id": f"res_{i}",
                "res": "success",
                "stat": "SUCCESS",
                "reason": "Demo Seed",
                "ts": ts,
                "det": "{}",
                "seq": sequence,
                "prev": prev_hash,
                "hash": row_hash
            })
            
            prev_hash = row_hash
            sequence += 1
            
        await conn.commit()
    
    print("Seeded 5 events.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_audit())
