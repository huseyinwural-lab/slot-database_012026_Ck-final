
import sqlite3
import os
import json

DB_PATH = "/app/backend/casino.db"
OUTPUT_FILE = "/app/artifacts/audit_tail_task3.txt"

def dump_audit():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    
    target_table = None
    if "audit_log" in tables:
        target_table = "audit_log"
    elif "auditlog" in tables:
        target_table = "auditlog"
    elif "audit_events" in tables:
        target_table = "audit_events"
    elif "auditevent" in tables:
        target_table = "auditevent"
    
    if not target_table:
        print(f"Error: Audit table not found. Tables: {tables}")
        conn.close()
        return

    print(f"Dumping last 50 rows from {target_table}...")
    
    try:
        query = f"SELECT * FROM {target_table} ORDER BY created_at DESC LIMIT 50;"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names
        col_names = [description[0] for description in cursor.description]

        with open(OUTPUT_FILE, "w") as f:
            f.write(f"--- Audit Log Dump ({target_table}) ---\n")
            f.write(f"Columns: {', '.join(col_names)}\n\n")
            for row in rows:
                row_dict = dict(zip(col_names, row))
                f.write(json.dumps(row_dict, default=str) + "\n")

        print(f"Successfully dumped {len(rows)} rows to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error dumping table {target_table}: {e}")
        # Try fallback if auditlog vs auditevent confusion
        if target_table == "auditlog" and "auditevent" in tables:
             print("Trying 'auditevent' instead...")
             # ... (simplified retry logic or just manual fix)
    
    conn.close()

if __name__ == "__main__":
    dump_audit()
