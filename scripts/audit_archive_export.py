import asyncio
import os
import argparse
import json
import gzip
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

# Setup DB
DATABASE_URL = settings.database_url

async def export_audit_log(target_date: str, output_dir: str):
    """
    Export audit logs for a specific date (YYYY-MM-DD) to a signed, compressed JSONL file.
    """
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    
    # Parse date
    try:
        start_dt = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.")
        return

    filename_base = f"audit_{target_date.replace('-', '')}"
    jsonl_path = os.path.join(output_dir, f"{filename_base}.jsonl.gz")
    manifest_path = os.path.join(output_dir, f"{filename_base}_manifest.json")
    sig_path = os.path.join(output_dir, f"{filename_base}_manifest.sig")
    
    os.makedirs(output_dir, exist_ok=True)

    print(f"Exporting logs from {start_dt} to {end_dt}...")
    
    row_count = 0
    file_sha256 = hashlib.sha256()

    async with engine.connect() as conn:
        # Fetch rows
        # In a real heavy DB, we'd use server-side cursors (stream). 
        # For now, fetching in chunks or all (if memory permits) is standard.
        # We'll use a simple fetch for MVP P0.
        query = text("""
            SELECT * FROM auditevent 
            WHERE timestamp >= :start AND timestamp < :end 
            ORDER BY timestamp ASC
        """)
        result = await conn.execute(query, {"start": start_dt, "end": end_dt})
        
        # Open Gzip file
        with gzip.open(jsonl_path, 'wt', encoding='utf-8') as f_out:
            for row in result.mappings():
                # Convert row to dict, handle datetime serialization
                data = dict(row)
                
                # Serialize datetimes
                for k, v in data.items():
                    if isinstance(v, datetime):
                        data[k] = v.isoformat()
                
                # Serialize JSON columns if they come as strings (SQLite) or Dicts
                # Assuming simple dict dump
                line = json.dumps(data) + "\n"
                f_out.write(line)
                
                # Update hash
                file_sha256.update(line.encode('utf-8'))
                row_count += 1

    print(f"Exported {row_count} rows to {jsonl_path}")
    
    # Create Manifest
    manifest = {
        "date": target_date,
        "file_name": os.path.basename(jsonl_path),
        "row_count": row_count,
        "sha256": file_sha256.hexdigest(),
        "schema_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat()
    }
    
    with open(manifest_path, 'w') as f_man:
        json.dump(manifest, f_man, indent=2)
        
    print(f"Manifest written to {manifest_path}")
    
    # Sign Manifest (HMAC-SHA256)
    secret = settings.audit_export_secret.encode()
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode()
    signature = hmac.new(secret, manifest_bytes, hashlib.sha256).hexdigest()
    
    with open(sig_path, 'w') as f_sig:
        f_sig.write(signature)
        
    print(f"Signature written to {sig_path}")
    await engine.dispose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Audit Log Archiver")
    parser.add_argument("--date", type=str, help="Date to export (YYYY-MM-DD)", default=(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"))
    parser.add_argument("--output", type=str, help="Output directory", default=settings.audit_archive_path)
    
    args = parser.parse_args()
    
    asyncio.run(export_audit_log(args.date, args.output))
