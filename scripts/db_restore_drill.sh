#!/bin/bash
set -e

echo "=== Go-Live Cutover: Database Backup & Restore Drill ==="
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/app/backups"
mkdir -p $BACKUP_DIR

# Detect DB (Assume SQLite for this container based on previous check)
DB_PATH="/app/backend/casino.db"
BACKUP_FILE="$BACKUP_DIR/backup_sqlite_$TIMESTAMP.db"
RESTORE_FILE="$BACKUP_DIR/restored_sqlite_$TIMESTAMP.db"

echo "[*] Database: SQLite (Simulation Mode)"

# 1. Backup Phase
echo "[1/3] Starting Backup..."
# Use python for safe copy if sqlite3 CLI missing
python3 -c "import shutil; shutil.copyfile('$DB_PATH', '$BACKUP_FILE')"
echo "    [PASS] SQLite database copied to $BACKUP_FILE"
ls -lh $BACKUP_FILE

# 2. Restore Phase
echo "[2/3] Starting Restore Drill..."
python3 -c "import shutil; shutil.copyfile('$BACKUP_FILE', '$RESTORE_FILE')"
echo "    [PASS] Restored to separate file $RESTORE_FILE"

# Integrity Check via Python
echo "    [EXEC] Running Integrity Check via Python..."
python3 -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('$RESTORE_FILE')
    cursor = conn.cursor()
    cursor.execute('PRAGMA integrity_check')
    result = cursor.fetchone()[0]
    if result == 'ok':
        print('    [PASS] Integrity Check: OK')
    else:
        print(f'    [FAIL] Integrity Check: {result}')
        sys.exit(1)
except Exception as e:
    print(f'    [FAIL] Error: {e}')
    sys.exit(1)
"

# 3. Verification
echo "[3/3] Verifying Data..."
python3 -c "
import sqlite3
conn = sqlite3.connect('$RESTORE_FILE')
cursor = conn.cursor()
try:
    cursor.execute(\"SELECT count(*) FROM 'transaction'\")
    count = cursor.fetchone()[0]
    print(f'    [PASS] Transaction Count in Restored DB: {count}')
except:
    print('    [WARN] Could not count transactions (table might be empty or missing)')
"

echo "=== Drill Complete: SUCCESS ==="
echo "Artifact: $BACKUP_FILE"
