import pytest
import os
import shutil
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import sys

# Ensure scripts in path
sys.path.append("/app/scripts")
from audit_archive_export import export_audit_log
from purge_audit_logs import purge_audit_logs
from restore_audit_logs import restore_audit_logs
from config import settings

@pytest.mark.asyncio
async def test_audit_lifecycle(session):
    # 1. Setup Data (Older than retention to trigger purge)
    # Retention is 90 days. We need data from 91 days ago.
    target_date = (datetime.now(timezone.utc) - timedelta(days=91)).strftime("%Y-%m-%d")
    
    # Use datetime object for insert to ensure consistent storage format with what SQLAlchemy/aiosqlite expects
    ts_obj = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc, hour=10)
    
    await session.execute(text("""
        INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, result, timestamp, row_hash, prev_row_hash, sequence)
        VALUES 
        (:id, 'r1', 'u1', 't1', 'LIFECYCLE_TEST', 'res', 'success', :ts, 'hash1', :prev, 1)
    """), {
        "id": "life_1",
        "ts": ts_obj,
        "prev": "0"*64
    })
    await session.commit()
    
    await session.close()
    
    # 2. Export (Archive)
    test_archive_path = "/tmp/test_audit_archive_storage"
    if os.path.exists(test_archive_path):
        shutil.rmtree(test_archive_path)
    
    # Patch settings
    settings.audit_archive_path = test_archive_path
    
    # Export
    await export_audit_log(target_date, output_dir="/tmp/audit_export_temp_lifecycle")
    
    # Verify File Exists in "Storage"
    date_path = datetime.strptime(target_date, "%Y-%m-%d").strftime("%Y/%m/%d")
    manifest_path = f"{test_archive_path}/audit/{date_path}/audit_{target_date}_part01_manifest.json"
    assert os.path.exists(manifest_path)
    
    # 3. Purge
    # Should delete the record because it is > 90 days and archived
    await purge_audit_logs(keep_days=90, dry_run=False)
    
    # Verify Deletion
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text(f"SELECT count(*) FROM auditevent WHERE id='life_1'"))
        count = res.scalar()
        assert count == 0
    await engine.dispose()
    
    # 4. Restore
    await restore_audit_logs(target_date, restore_to_db=True)
    
    # Verify Restoration
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text(f"SELECT count(*) FROM auditevent WHERE id='life_1'"))
        count = res.scalar()
        assert count == 1
    await engine.dispose()
