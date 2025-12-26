import asyncio
import argparse
import sys
import os
import json
import hashlib
import hmac
import gzip
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
from config import settings
from app.ops.storage import get_storage_client

DATABASE_URL = settings.database_url

async def restore_audit_logs(target_date: str, restore_to_db: bool = False):
    print(f"Restoring audit logs for {target_date}...")
    storage = get_storage_client()
    
    # Path
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    except:
        print("Invalid date.")
        return

    date_path = dt.strftime("%Y/%m/%d")
    remote_prefix = f"{settings.audit_archive_prefix.strip('/')}/{date_path}"
    
    # Files
    manifest_key = f"{remote_prefix}/audit_{target_date}_part01_manifest.json"
    data_key = f"{remote_prefix}/audit_{target_date}_part01.jsonl.gz"
    
    if not storage.exists(manifest_key) or not storage.exists(data_key):
        print(f"Archive not found for {target_date}")
        return

    # Verify Manifest
    manifest_bytes = storage.get_object(manifest_key)
    manifest = json.loads(manifest_bytes)
    
    secret = settings.audit_export_secret.encode()
    stored_sig = manifest.get('signature')
    calc_sig = hmac.new(secret, manifest['sha256'].encode(), hashlib.sha256).hexdigest()
    
    if stored_sig != calc_sig:
        print("Signature mismatch!")
        return
    print("Signature Verified.")
    
    # Verify Data Hash
    data_bytes = storage.get_object(data_key)
    # Note: data_key content is gzipped. Hash in manifest is sha256(jsonl_lines_uncompressed) or compressed?
    # In `export_audit_log`, we calculated hash on the lines *before* gzipping?
    # Wait, `file_sha256.update(line.encode('utf-8'))`. `f_out` is `gzip.open`.
    # So `line` is uncompressed.
    # But wait, `file_sha256` was calculated on uncompressed data.
    # So we must decompress to verify hash.
    
    decompressed_data = gzip.decompress(data_bytes)
    calc_data_hash = hashlib.sha256(decompressed_data).hexdigest()
    # Wait, `file_sha256` in export update() calls `line.encode`. `line` has `\n`.
    # `gzip.decompress` returns bytes matching the concatenation of all lines.
    # So hashing decompressed bytes should match.
    
    # In export script:
    # `line = json.dumps(data) + "\n"`
    # `f_out.write(line)` (gzip stream)
    # `file_sha256.update(line.encode('utf-8'))`
    
    if calc_data_hash != manifest['sha256']:
        print("Data Hash Mismatch!")
        # Debug
        # print(f"Calc: {calc_data_hash}")
        # print(f"Manifest: {manifest['sha256']}")
        return
    print("Data Hash Verified.")
    
    events = []
    for line in decompressed_data.decode('utf-8').splitlines():
        if line.strip():
            events.append(json.loads(line))
            
    print(f"Loaded {len(events)} events.")
    
    if restore_to_db:
        print(f"Restoring to {DATABASE_URL}...")
        engine = create_async_engine(DATABASE_URL)
        async with engine.begin() as conn:
            # We need to handle duplicates. `INSERT OR IGNORE` or check existence.
            # And `timestamp` parsing.
            count = 0
            for e in events:
                # Check exist
                res = await conn.execute(text("SELECT 1 FROM auditevent WHERE id = :id"), {"id": e['id']})
                if res.scalar():
                    continue
                
                # Insert
                # Map fields
                await conn.execute(text("""
                    INSERT INTO auditevent 
                    (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp, details, sequence, prev_row_hash, row_hash)
                    VALUES 
                    (:id, :rid, :actor, :tid, :act, :res_type, :res_id, :res, :stat, :reason, :ts, :det, :seq, :prev, :hash)
                """), {
                    "id": e['id'],
                    "rid": e['request_id'],
                    "actor": e['actor_user_id'],
                    "tid": e['tenant_id'],
                    "act": e['action'],
                    "res_type": e['resource_type'],
                    "res_id": e['resource_id'],
                    "res": e['result'],
                    "stat": e['status'],
                    "reason": e['reason'],
                    "ts": datetime.fromisoformat(e['timestamp']),
                    "det": json.dumps(e['details']),
                    "seq": e['sequence'],
                    "prev": e['prev_row_hash'],
                    "hash": e['row_hash']
                })
                count += 1
            print(f"Restored {count} events.")
        await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=True)
    parser.add_argument("--restore-to-db", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(restore_audit_logs(args.date, args.restore_to_db))
