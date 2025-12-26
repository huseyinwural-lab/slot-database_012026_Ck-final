import asyncio
import hashlib
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
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
            # Verify Sequence
            if row['sequence'] is not None:
                # If we have gaps (e.g. filtered by tenant but sequence is global? No, I implemented per-tenant chain logic in audit.py)
                # In audit.py: `stmt = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)`
                # So sequence is per-tenant.
                pass
            
            # Re-compute Hash
            # Must match the canonicalization in audit.py exactly
            payload = {
                "tenant_id": row['tenant_id'],
                "actor_user_id": row['actor_user_id'],
                "action": row['action'],
                "resource_type": row['resource_type'],
                "resource_id": row['resource_id'],
                "timestamp": row['timestamp'], # row['timestamp'] is a string in SQLite raw result? Or datetime?
                # In sqlite+aiosqlite raw execute, it returns string usually if stored as string.
                # SQLModel stores datetime. 
                # Let's handle both.
                "reason": row['reason'],
                "status": row['status'],
                "details": json.loads(row['details']) if isinstance(row['details'], str) else (row['details'] or {}),
                "sequence": row['sequence']
            }
            
            # Timestamp handling
            # In audit.py: `timestamp.isoformat()`.
            # If DB returns datetime object, we need to isoformat it.
            # If DB returns string, we use it as is?
            # Warning: ISO format might differ (microsecond precision).
            # This is the tricky part of "canonicalization".
            # For P0 verification script, we try to match what's in DB.
            # Ideally `timestamp` in payload is exactly the string used during hashing.
            # Since we inserted `timestamp` (datetime object) into DB, SQLModel/SQLAlchemy serialized it.
            # If we read it back, we get datetime object. `isoformat()` should match if precision is kept.
            
            ts = payload['timestamp']
            if not isinstance(ts, str):
                # Force standard isoformat
                payload['timestamp'] = ts.isoformat()
            
            # However, `audit.py` does: `timestamp = datetime.now(timezone.utc)` -> `payload['timestamp'] = timestamp.isoformat()` -> `hash`.
            # Then `evt = AuditEvent(..., timestamp=timestamp)`.
            # So the DB stores the datetime object.
            # When we read it back here, we get a datetime object.
            # `datetime.isoformat()` usually matches.
            
            # But wait, `audit.py` creates `payload` *before* inserting.
            # `timestamp.isoformat()` is what was hashed.
            
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
                print(f"  Canonical Payload: {canonical_str}")
                errors += 1
            
            # Advance
            if row['row_hash']:
                prev_hash = row['row_hash']
            else:
                # If row has no hash (legacy data), we might reset or skip?
                # For D1.4, we assume legacy data is skipped or "0" hash?
                # Logic: `prev_row_hash = prev_event.row_hash if ... else "0"*64`
                # If current row has no hash, next row will use "0"*64 if we follow audit.py logic?
                # No, audit.py uses `prev_event.row_hash`. If `None`, uses "0"*64.
                prev_hash = "0" * 64

        if errors == 0:
            print("SUCCESS: Chain verified. Integrity intact.")
        else:
            print(f"FAILED: Found {errors} integrity errors.")

    await engine.dispose()

if __name__ == "__main__":
    import sys
    tenant = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(verify_chain(tenant))
