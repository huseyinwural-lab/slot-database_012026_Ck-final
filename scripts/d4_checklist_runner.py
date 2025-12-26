import asyncio
import os
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings
import shutil

# --- D4-1: Secrets & Env Sanitization ---
def generate_env_dump():
    print("Generating Sanitized Env Dump...")
    sanitized = []
    # List of sensitive keys based on config.py
    sensitive = [
        "JWT_SECRET", "STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET", 
        "ADYEN_API_KEY", "ADYEN_HMAC_KEY", "OPENAI_API_KEY", 
        "SENDGRID_API_KEY", "AUDIT_EXPORT_SECRET", "AUDIT_S3_SECRET_KEY",
        "EMERGENT_LLM_KEY"
    ]
    
    # Read from os.environ or config settings
    # We'll iterate the config object
    for key, value in settings.dict().items():
        key_upper = key.upper()
        if any(s in key_upper for s in sensitive) or "KEY" in key_upper or "SECRET" in key_upper:
            masked = f"{str(value)[:4]}...***" if value else "Not Set"
            sanitized.append(f"{key_upper}={masked}")
        else:
            sanitized.append(f"{key_upper}={value}")
            
    with open("/app/artifacts/d4_env_dump_sanitized.txt", "w") as f:
        f.write("\n".join(sorted(sanitized)))
    print("Env dump saved.")

# --- D4-1: DB & Migration Verification ---
async def verify_db_migration():
    print("Verifying DB Migrations...")
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        # Check alembic version
        try:
            res = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = res.scalar()
            status = f"Alembic Head: {version}"
        except Exception as e:
            status = f"Alembic Table Missing or Error: {e}"
            
        # Check critical tables
        tables = ["ledgertransaction", "payoutattempt", "auditevent", "robotdefinition", "callbacknonce", "game"]
        table_status = []
        for t in tables:
            try:
                await conn.execute(text(f"SELECT 1 FROM {t} LIMIT 1"))
                table_status.append(f"{t}: OK")
            except Exception:
                table_status.append(f"{t}: MISSING")
                
    output = f"""DB Verification Timestamp: {datetime.now(timezone.utc)}
{status}

Critical Tables:
{chr(10).join(table_status)}
"""
    with open("/app/artifacts/d4_db_migration_verification.txt", "w") as f:
        f.write(output)
    await engine.dispose()
    print("DB Verification saved.")

# --- D4-1: Backup/Restore Drill ---
async def backup_restore_drill():
    print("Running Backup/Restore Drill...")
    original_db = "/app/backend/casino.db"
    backup_path = "/app/artifacts/casino_backup.db"
    restore_path = "/app/artifacts/casino_restored.db"
    
    log = []
    
    # 1. Backup (Copy file)
    try:
        shutil.copy2(original_db, backup_path)
        log.append(f"Backup created at {backup_path}")
    except Exception as e:
        log.append(f"Backup FAILED: {e}")
        return

    # 2. Restore (Copy back to alternate location)
    try:
        shutil.copy2(backup_path, restore_path)
        log.append(f"Restored to {restore_path}")
    except Exception as e:
        log.append(f"Restore FAILED: {e}")
        return
        
    # 3. Verify Restore
    restore_url = f"sqlite+aiosqlite:///{restore_path}"
    engine = create_async_engine(restore_url)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT count(*) FROM auditevent"))
            count = res.scalar()
            log.append(f"Verification: Found {count} audit events in restored DB.")
            if count > 0:
                log.append("STATUS: PASS")
            else:
                log.append("STATUS: WARNING (Empty DB?)")
    except Exception as e:
        log.append(f"Verification FAILED: {e}")
    finally:
        await engine.dispose()
        
    with open("/app/artifacts/d4_backup_restore_logs.txt", "w") as f:
        f.write("\n".join(log))
    print("Backup Drill complete.")

if __name__ == "__main__":
    generate_env_dump()
    asyncio.run(verify_db_migration())
    asyncio.run(backup_restore_drill())
