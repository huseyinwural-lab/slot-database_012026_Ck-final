
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

    for table in ["auditevent", "auditlog"]:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [r[1] for r in cursor.fetchall()]
            if not columns:
                continue
            
            print(f"Checking table {table}, columns: {columns}")
            
            sort_col = "created_at" if "created_at" in columns else "timestamp" if "timestamp" in columns else None
            
            if sort_col:
                query = f"SELECT * FROM {table} ORDER BY {sort_col} DESC LIMIT 50;"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                with open(OUTPUT_FILE, "w") as f:
                    f.write(f"--- Audit Log Dump ({table}) ---\n")
                    f.write(f"Columns: {', '.join(columns)}\n\n")
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        f.write(json.dumps(row_dict, default=str) + "\n")
                
                print(f"Successfully dumped {len(rows)} rows from {table} to {OUTPUT_FILE}")
                return
        except Exception as e:
            print(f"Error checking {table}: {e}")

    conn.close()

if __name__ == "__main__":
    dump_audit()
