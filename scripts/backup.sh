#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

# Detect DB Type from Env
if [[ "$DATABASE_URL" == *"postgresql"* ]]; then
    echo "🔵 Detected PostgreSQL..."
    # Extract params from DATABASE_URL or use pg_dump directly if env vars set
    # Assuming pg_dump is available and credentials are in env or .pgpass
    # Simple file dump
    FILENAME="$BACKUP_DIR/db_backup_$DATE.sql.gz"
    pg_dump "$DATABASE_URL" | gzip > "$FILENAME"
    echo "✅ Backup created: $FILENAME"
    
elif [[ "$DATABASE_URL" == *"sqlite"* ]]; then
    echo "🟢 Detected SQLite..."
    # Extract path from URL (sqlite+aiosqlite:////path/to/db)
    # Remove prefix
    DB_PATH=$(echo "$DATABASE_URL" | sed 's/sqlite+aiosqlite:\/\/\///')
    FILENAME="$BACKUP_DIR/sqlite_backup_$DATE.db"
    
    # Use sqlite3 backup command for safety
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$DB_PATH" ".backup '$FILENAME'"
    else
        cp "$DB_PATH" "$FILENAME"
    fi
    gzip "$FILENAME"
    echo "✅ Backup created: $FILENAME.gz"
    
else
    echo "❌ Unknown Database Type"
    exit 1
fi

# Cleanup old backups
find "$BACKUP_DIR" -type f -name "*_backup_*" -mtime +$RETENTION_DAYS -delete
echo "🧹 Cleaned up backups older than $RETENTION_DAYS days"
