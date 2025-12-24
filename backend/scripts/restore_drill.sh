#!/bin/bash
set -e

DB_FILE="casino.db"
BACKUP_FILE="casino.db.bak"

echo "=== STARTING RESTORE DRILL ==="

# 1. Create Backup
echo "[1] Creating backup..."
cp $DB_FILE $BACKUP_FILE
ls -l $BACKUP_FILE

# 2. Simulate Data Loss
echo "[2] Simulating data loss (renaming original)..."
mv $DB_FILE "${DB_FILE}.lost"

# 3. Restore
echo "[3] Restoring from backup..."
cp $BACKUP_FILE $DB_FILE

# 4. Verify
echo "[4] Verifying integrity..."
if [ -f "$DB_FILE" ]; then
    echo "PASS: Database file restored."
    # Optional: Run a simple query
    python3 -c "import sqlite3; conn=sqlite3.connect('$DB_FILE'); print(conn.execute('SELECT 1').fetchone())"
else
    echo "FAIL: Database file missing."
    exit 1
fi

# Cleanup
rm $BACKUP_FILE
rm "${DB_FILE}.lost"

echo "=== RESTORE DRILL COMPLETE: PASS ==="
