import asyncio
import argparse
import sys
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
from config import settings
from app.ops.storage import get_storage_client

DATABASE_URL = settings.database_url

async def purge_audit_logs(keep_days: int = 90, force: bool = False, dry_run: bool = False):
    """
    Purge audit logs older than keep_days, ONLY if verified in remote archive.
    """
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    storage = get_storage_client()
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    
    print(f"Purge Policy: Keep {keep_days} days (Cutoff: {cutoff_str})")
    
    # 1. Identify candidate dates (e.g. iterate last 365 days up to keep_days ago)
    # Ideally query distinct dates from DB < cutoff
    # SQLite/Postgres: SELECT DISTINCT date(timestamp) ...
    # For compatibility, let's just query min date.
    
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT min(timestamp) FROM auditevent"))
        min_ts = res.scalar()
        
        if not min_ts:
            print("No audit logs found.")
            await engine.dispose()
            return

        # Ensure min_ts is datetime
        if isinstance(min_ts, str):
            min_ts = datetime.fromisoformat(min_ts)
        
        # Iterate day by day
        current_date = min_ts.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date < cutoff_date:
            date_str = current_date.strftime("%Y-%m-%d")
            print(f"Checking {date_str}...")
            
            # Check Remote Archive
            date_path = current_date.strftime("%Y/%m/%d")
            remote_prefix = f"{settings.audit_archive_prefix.strip('/')}/{date_path}"
            manifest_key = f"{remote_prefix}/audit_{date_str}_part01_manifest.json"
            
            if not storage.exists(manifest_key):
                print(f"  [SKIP] Remote archive not found for {date_str}. (Key: {manifest_key})")
                current_date += timedelta(days=1)
                continue
                
            # Verify Manifest
            try:
                manifest_bytes = storage.get_object(manifest_key)
                manifest = json.loads(manifest_bytes)
                
                # Verify Signature
                secret = settings.audit_export_secret.encode()
                stored_sig = manifest.get('signature')
                calc_sig = hmac.new(secret, manifest['sha256'].encode(), hashlib.sha256).hexdigest()
                
                if stored_sig != calc_sig:
                    print(f"  [SKIP] Signature mismatch for {date_str}.")
                    current_date += timedelta(days=1)
                    continue
                    
                # Ideally Verify Chain (Head/Tail) against DB if we want ultra-paranoia
                # But if signature matches secret, we trust the export was done by us.
                
                # Purge
                if not dry_run:
                    # Need to disable trigger or use specific permission? 
                    # D1: "DELETE auditevent ... -> FAIL".
                    # We need a way to bypass. 
                    # Options: 
                    # 1. DROP TRIGGER, DELETE, CREATE TRIGGER (Dangerous if concurrent writes)
                    # 2. Add specific condition to Trigger (e.g. IF actor != 'PURGE_JOB') -> SQLite triggers difficult.
                    # 3. Use 'system' user logic?
                    # D1 task said: "Sadece istisna: “legal purge” ... partition drop veya arşiv sonrası delete".
                    # In SQLite, we can drop trigger temporarily.
                    
                    print(f"  [PURGE] Deleting logs for {date_str}...")
                    
                    # Transactional drop/delete/create
                    async with conn.begin(): # Nested transaction
                        if "sqlite" in DATABASE_URL:
                            await conn.execute(text("DROP TRIGGER IF EXISTS prevent_audit_delete"))
                        
                        # Delete
                        del_query = text("DELETE FROM auditevent WHERE timestamp >= :start AND timestamp < :end")
                        next_day = current_date + timedelta(days=1)
                        res = await conn.execute(del_query, {"start": current_date, "end": next_day})
                        print(f"    Deleted {res.rowcount} rows.")
                        
                        # Restore trigger
                        if "sqlite" in DATABASE_URL:
                            await conn.execute(text("""
                                CREATE TRIGGER IF NOT EXISTS prevent_audit_delete 
                                BEFORE DELETE ON auditevent 
                                BEGIN 
                                    SELECT RAISE(ABORT, 'Audit events are immutable: DELETE blocked'); 
                                END;
                            """))
                            
                        # Log Audit Event for Purge? (Recursive?)
                        # We should log it, but it's a new day's event, so it won't be deleted by this purge.
                        # We can do it after transaction commits or rely on app level log.
                else:
                    print(f"  [DRY-RUN] Would delete logs for {date_str}")

            except Exception as e:
                print(f"  [ERROR] Verification failed: {e}")
            
            current_date += timedelta(days=1)

    await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-days", type=int, default=settings.audit_retention_days)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(purge_audit_logs(args.keep_days, dry_run=args.dry_run))
