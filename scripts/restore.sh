#!/bin/bash
set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh <backup_file_path>"
    exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE the current database."
echo "Press Ctrl+C to cancel or wait 5 seconds..."
sleep 5

if [[ "$DATABASE_URL" == *"sqlite"* ]]; then
    echo "🟢 Restoring SQLite..."
    DB_PATH=$(echo "$DATABASE_URL" | sed 's/sqlite+aiosqlite:\/\/\///')
    
    # Gunzip to temp
    gunzip -c "$BACKUP_FILE" > "/tmp/restore.db"
    mv "/tmp/restore.db" "$DB_PATH"
    echo "✅ Restore complete."
    
else
    echo "🔵 Restoring PostgreSQL..."
    # Drop and recreate schema usually required, or psql -f
    gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"
    echo "✅ Restore complete."
fi
