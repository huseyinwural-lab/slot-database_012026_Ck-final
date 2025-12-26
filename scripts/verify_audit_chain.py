import asyncio
import hashlib
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
import os

# Fix path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
from config import settings

DATABASE_URL = settings.database_url

async def verify_chain(tenant_id: str = None):
    print(f"Verifying Audit Chain for DB: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        query = "SELECT * FROM auditevent"
        params = {}
        if tenant_id:
            query += " WHERE tenant_id = :tid"
            params["tid"] = tenant_id
        
        query += " ORDER BY sequence ASC"
        
        result = await conn.execute(text(query), params)
        rows = result.mappings().all()
        
        print(f"Found {len(rows)} events.")
        
        prev_hash = "0" * 64
        errors = 0
        
        for i, row in enumerate(rows):
            if row['sequence'] is None:
                continue # Skip legacy
                
            payload = {
                "tenant_id": row['tenant_id'],
                "actor_user_id": row['actor_user_id'],
                "action": row['action'],
                "resource_type": row['resource_type'],
                "resource_id": row['resource_id'],
                "timestamp": row['timestamp'],
                "reason": row['reason'],
                "status": row['status'],
                "details": json.loads(row['details']) if isinstance(row['details'], str) else (row['details'] or {}),
                "sequence": row['sequence']
            }
            
            # Timestamp handling
            ts = payload['timestamp']
            # If datetime, format it. If string, use it.
            if not isinstance(ts, str):
                payload['timestamp'] = ts.isoformat()
            
            canonical_str = json.dumps(payload, sort_keys=True)
            
            # Check prev hash
            if row['prev_row_hash'] and row['prev_row_hash'] != prev_hash:
                print(f"FAIL: Row {row['id']} (Seq {row['sequence']}): Prev hash mismatch.")
                print(f"  Expected: {prev_hash}")
                print(f"  Found:    {row['prev_row_hash']}")
                errors += 1
            
            # Calc current
            curr_hash = hashlib.sha256((prev_hash + canonical_str).encode('utf-8')).hexdigest()
            
            if row['row_hash'] and row['row_hash'] != curr_hash:
                print(f"FAIL: Row {row['id']} (Seq {row['sequence']}): Hash mismatch.")
                print(f"  Computed: {curr_hash}")
                print(f"  Stored:   {row['row_hash']}")
                errors += 1
            
            if row['row_hash']:
                prev_hash = row['row_hash']
            else:
                prev_hash = "0" * 64

        if errors == 0:
            print("SUCCESS: Chain verified. Integrity intact.")
        else:
            print(f"FAILED: Found {errors} integrity errors.")

    await engine.dispose()

if __name__ == "__main__":
    tenant = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(verify_chain(tenant))
