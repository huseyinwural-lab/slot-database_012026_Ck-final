import pytest
import os
import json
import gzip
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy import text

@pytest.mark.asyncio
async def test_audit_archive_export_script(session):
    # 1. Seed Data for "Yesterday"
    yesterday = datetime.now(timezone.utc).date() # Current date actually, for simplicity in test env
    # Use today's date for test, since export script defaults to yesterday but we can pass arg
    
    target_date = yesterday.strftime("%Y-%m-%d")
    
    await session.execute(text(f"""
        INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, result, timestamp)
        VALUES 
        ('exp_1', 'r1', 'u1', 't1', 'EXPORT_TEST', 'res', 'success', '{target_date} 10:00:00'),
        ('exp_2', 'r2', 'u1', 't1', 'EXPORT_TEST', 'res', 'success', '{target_date} 11:00:00')
    """))
    await session.commit()
    
    # 2. Run Script (subprocess)
    import subprocess
    output_dir = "/tmp/audit_test_archive"
    
    cmd = f"python3 /app/scripts/audit_archive_export.py --date {target_date} --output {output_dir}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "Exported" in result.stdout
    
    # 3. Verify Output
    filename_base = f"audit_{target_date.replace('-', '')}"
    jsonl_path = os.path.join(output_dir, f"{filename_base}.jsonl.gz")
    manifest_path = os.path.join(output_dir, f"{filename_base}_manifest.json")
    
    assert os.path.exists(jsonl_path)
    assert os.path.exists(manifest_path)
    
    # Check JSONL content
    count = 0
    with gzip.open(jsonl_path, 'rt') as f:
        for line in f:
            data = json.loads(line)
            if data['id'] in ['exp_1', 'exp_2']:
                count += 1
    
    # Might be more than 2 if other tests ran, but at least 2
    assert count >= 2
    
    # Check Manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        assert manifest['date'] == target_date
        assert manifest['row_count'] >= 2
