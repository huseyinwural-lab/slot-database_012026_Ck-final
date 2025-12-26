import asyncio
import os
import argparse
import json
import gzip
import hashlib
import hmac
import sys
import io
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Ensure backend directory is in path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from config import settings
from app.ops.storage import get_storage_client

# Setup DB
DATABASE_URL = settings.database_url

async def export_audit_log(target_date: str, output_dir: str = None, db_url: str = None):
    """
    Export audit logs for a specific date (YYYY-MM-DD) to a signed, compressed JSONL file,
    and upload to configured remote storage.
    """
    url = db_url or DATABASE_URL
    print(f"Connecting to {url}...")
    engine = create_async_engine(url)
    storage = get_storage_client()
    
    # Parse date
    try:
        # Use naive datetime for query to be safe with SQLite default storage
        start_dt = datetime.strptime(target_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=1)
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.")
        return

    # Prepare local temp storage (or use output_dir if provided for local testing)
    temp_dir = output_dir or "/tmp/audit_export_temp"
    os.makedirs(temp_dir, exist_ok=True)

    # Path logic
    date_path = start_dt.strftime("%Y/%m/%d")
    filename_base = f"audit_{target_date}_part01"
    
    local_jsonl = os.path.join(temp_dir, f"{filename_base}.jsonl.gz")
    local_manifest = os.path.join(temp_dir, f"{filename_base}_manifest.json")
    local_sig = os.path.join(temp_dir, f"{filename_base}.jsonl.gz.sig")
    local_sha256 = os.path.join(temp_dir, f"{filename_base}.jsonl.gz.sha256")

    print(f"Exporting logs from {start_dt} to {end_dt}...")
    
    row_count = 0
    file_sha256 = hashlib.sha256()
    
    chain_head_hash = None
    chain_tail_hash = None

    async with engine.connect() as conn:
        # We try strict comparison. SQLite '2025...' string vs :start param.
        # If DB has ISO strings, we should pass ISO strings.
        query = text("""
            SELECT * FROM auditevent 
            WHERE timestamp >= :start AND timestamp < :end 
            ORDER BY timestamp ASC, sequence ASC
        """)
        # Pass strings explicitly if SQLite
        if "sqlite" in url:
             result = await conn.execute(query, {"start": start_dt.isoformat(), "end": end_dt.isoformat()})
        else:
             result = await conn.execute(query, {"start": start_dt, "end": end_dt})
        
        # Open Gzip file
        with gzip.open(local_jsonl, 'wt', encoding='utf-8') as f_out:
            rows = result.mappings().all()
            for i, row in enumerate(rows):
                data = dict(row)
                
                # Chain tracking
                if i == 0:
                    chain_head_hash = data.get('row_hash')
                if i == len(rows) - 1:
                    chain_tail_hash = data.get('row_hash')

                # Serialize datetimes
                for k, v in data.items():
                    if isinstance(v, datetime):
                        data[k] = v.isoformat()
                
                line = json.dumps(data) + "\n"
                f_out.write(line)
                
                file_sha256.update(line.encode('utf-8'))
                row_count += 1

    print(f"Exported {row_count} rows to local temp: {local_jsonl}")
    
    if row_count == 0:
        print("No rows found. Skipping upload.")
        await engine.dispose()
        return

    # SHA256 File
    final_sha256 = file_sha256.hexdigest()
    with open(local_sha256, 'w') as f:
        f.write(final_sha256)

    # Manifest
    manifest = {
        "date": target_date,
        "parts": 1,
        "part_index": 1,
        "file_name": f"{filename_base}.jsonl.gz",
        "row_count": row_count,
        "sha256": final_sha256,
        "chain_head_hash": chain_head_hash,
        "chain_tail_hash": chain_tail_hash,
        "schema_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat()
    }
    
    with open(local_manifest, 'w') as f_man:
        json.dump(manifest, f_man, indent=2)
    
    # Signature (HMAC of Manifest)
    secret = settings.audit_export_secret.encode()
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode()
    signature = hmac.new(secret, manifest_bytes, hashlib.sha256).hexdigest()
    
    data_signature = hmac.new(secret, final_sha256.encode(), hashlib.sha256).hexdigest()
    manifest['signature'] = data_signature
    
    # Rewrite manifest with signature
    with open(local_manifest, 'w') as f_man:
        json.dump(manifest, f_man, indent=2)

    # Upload to Storage
    # Path: audit/YYYY/MM/DD/filename
    remote_prefix = f"{settings.audit_archive_prefix.strip('/')}/{date_path}"
    
    print(f"Uploading to {settings.audit_archive_backend} at {remote_prefix}...")
    
    files_to_upload = [local_jsonl, local_manifest, local_sha256]
    
    for fpath in files_to_upload:
        fname = os.path.basename(fpath)
        remote_key = f"{remote_prefix}/{fname}"
        print(f"  Uploading {fname} -> {remote_key}")
        with open(fpath, "rb") as f_in:
            storage.put_object(remote_key, f_in)
            
    print("Upload complete.")
    
    if not output_dir:
        import shutil
        shutil.rmtree(temp_dir)
        
    await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Audit Log Archiver & Upload")
    parser.add_argument("--date", type=str, help="Date to export (YYYY-MM-DD)", default=(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"))
    parser.add_argument("--output", type=str, help="Local output directory (optional, mainly for dev)", default=None)
    parser.add_argument("--db-url", type=str, help="Database URL override", default=None)
    
    args = parser.parse_args()
    
    asyncio.run(export_audit_log(args.date, args.output, args.db_url))
