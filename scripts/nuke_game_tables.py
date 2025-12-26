import sqlite3
import os

db_path = '/app/backend/casino.db'
if os.path.exists(db_path):
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('DROP TABLE IF EXISTS game')
        print("Dropped table 'game'.")
        # Also drop child tables if needed? 
        # gamesession, gameround likely reference it. 
        # In SQLite, FK constraints might not enforce drop unless enabled.
        # But for schema sync, dropping game is enough if we recreate it.
        
        # We should also drop dependent tables to be clean
        conn.execute('DROP TABLE IF EXISTS gamesession')
        conn.execute('DROP TABLE IF EXISTS gameround')
        conn.execute('DROP TABLE IF EXISTS gamerobotbinding')
        print("Dropped dependent tables.")
        
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("DB not found.")