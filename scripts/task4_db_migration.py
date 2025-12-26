
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
        # Check columns
        print("Checking 'auditevent' table...")
        
        # SQLite pragma
        if "sqlite" in DATABASE_URL:
            result = await conn.execute(text("PRAGMA table_info(auditevent)"))
            columns = [row.name for row in result.fetchall()]
        else:
            # Postgres (fallback logic if env changes)
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='auditevent'"
            ))
            columns = [row.column_name for row in result.fetchall()]
            
        print(f"Current columns: {columns}")
        
        # Columns to add
        # Name, Type
        to_add = [
            ("reason", "TEXT"),
            ("actor_role", "TEXT"),
            ("user_agent", "TEXT"),
            ("before_json", "JSON"),
            ("after_json", "JSON"),
            ("diff_json", "JSON"),
            ("metadata_json", "JSON"),
            ("error_code", "TEXT"),
            ("error_message", "TEXT"),
            ("status", "TEXT") # User asked for 'status' (SUCCESS/DENIED/FAILED), current model has 'result'. I will map 'result' to 'status' conceptually or alias.
            # actually 'result' exists. User asked for 'status'. Let's add 'status' and maybe migrate 'result' data to it, or just use 'status' moving forward.
            # "result" is already in the model. User listed "status (SUCCESS | DENIED | FAILED)".
            # I will add 'status' to be compliant with the spec.
        ]
        
        for col_name, col_type in to_add:
            if col_name not in columns:
                print(f"Adding column {col_name} ({col_type})...")
                # SQLite JSON is just TEXT usually, but let's use appropriate type syntax
                # For SQLite, we can just use TEXT for JSON if we want to be safe, or JSON if supported.
                # SQLAlchemy handles JSON serialization.
                
                type_sql = col_type
                if "sqlite" in DATABASE_URL and col_type == "JSON":
                    type_sql = "TEXT" # SQLite stores JSON as TEXT
                
                try:
                    await conn.execute(text(f"ALTER TABLE auditevent ADD COLUMN {col_name} {type_sql}"))
                    print(f"Added {col_name}.")
                except Exception as e:
                    print(f"Failed to add {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists.")

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
