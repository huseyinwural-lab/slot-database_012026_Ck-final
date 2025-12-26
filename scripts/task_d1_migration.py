import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Env
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:////app/backend/casino.db")

async def migrate():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("1. Checking 'auditevent' schema for Hash Chaining columns...")
        
        # Check current columns
        if "sqlite" in DATABASE_URL:
            result = await conn.execute(text("PRAGMA table_info(auditevent)"))
            columns = [row.name for row in result.fetchall()]
        else:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='auditevent'"
            ))
            columns = [row.column_name for row in result.fetchall()]
            
        print(f"Current columns: {columns}")
        
        to_add = [
            ("row_hash", "TEXT"),
            ("prev_row_hash", "TEXT"),
            ("chain_id", "TEXT"),
            ("sequence", "INTEGER")
        ]
        
        for col_name, col_type in to_add:
            if col_name not in columns:
                print(f"Adding column {col_name} ({col_type})...")
                # SQLite
                type_sql = col_type
                try:
                    await conn.execute(text(f"ALTER TABLE auditevent ADD COLUMN {col_name} {type_sql}"))
                    print(f"Added {col_name}.")
                except Exception as e:
                    print(f"Failed to add {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists.")

        # 2. Add Triggers (D1.1)
        print("2. Adding Immutable Triggers (D1.1)...")
        if "sqlite" in DATABASE_URL:
            triggers = [
                """
                CREATE TRIGGER IF NOT EXISTS prevent_audit_update 
                BEFORE UPDATE ON auditevent 
                BEGIN 
                    SELECT RAISE(ABORT, 'Audit events are immutable: UPDATE blocked'); 
                END;
                """,
                """
                CREATE TRIGGER IF NOT EXISTS prevent_audit_delete 
                BEFORE DELETE ON auditevent 
                BEGIN 
                    SELECT RAISE(ABORT, 'Audit events are immutable: DELETE blocked'); 
                END;
                """
            ]
            for t in triggers:
                try:
                    await conn.execute(text(t))
                    print("Trigger created/verified.")
                except Exception as e:
                    print(f"Failed to create trigger: {e}")
        else:
            print("Skipping triggers for non-SQLite DB (needs manual implementation or different syntax).")

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
