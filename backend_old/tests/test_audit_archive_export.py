import pytest
import os
import json
from datetime import datetime, timezone
from sqlalchemy import text
import sys

# Import script module (add scripts dir to path)
sys.path.append("/app/scripts")
from audit_archive_export import export_audit_log

@pytest.mark.asyncio
async def test_audit_archive_export_script(session):
    # 1. Seed Data
    yesterday = datetime.now(timezone.utc).date()
    target_date = yesterday.strftime("%Y-%m-%d")
    
    await session.execute(text(f"""
        INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, result, timestamp)
        VALUES 
        ('exp_1', 'r1', 'u1', 't1', 'EXPORT_TEST', 'res', 'success', '{target_date} 10:00:00'),
        ('exp_2', 'r2', 'u1', 't1', 'EXPORT_TEST', 'res', 'success', '{target_date} 11:00:00')
    """))
    await session.commit()
    
    # Close session to release locks before subprocess/separate engine
    await session.close()
    
    # 2. Run Function Directly
    # Fallback to config if session URL isn't available, or assuming standard DB
    db_url = "sqlite+aiosqlite:////app/backend/casino.db"

    output_dir = "/tmp/audit_test_archive"
    
    await export_audit_log(target_date, output_dir, db_url)
    
    # 3. Verify Output
    filename_base = f"audit_{target_date.replace('-', '')}"
    jsonl_path = os.path.join(output_dir, f"{filename_base}.jsonl.gz")
    manifest_path = os.path.join(output_dir, f"{filename_base}_manifest.json")
    
    assert os.path.exists(jsonl_path)
    assert os.path.exists(manifest_path)
    
    # Check Manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        assert manifest['date'] == target_date
        # We expect at least 2 rows
        assert manifest['row_count'] >= 2
