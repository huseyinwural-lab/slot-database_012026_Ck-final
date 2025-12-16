#!/usr/bin/env bash
set -euo pipefail

# Restore postgres from a gzip sql dump.
# Usage: ./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz

FILE="${1:-}"
if [ -z "$FILE" ]; then
  echo "Usage: $0 <backup.sql.gz>"
  exit 2
fi

cd "$(dirname "$0")/.."

echo "Restoring from: $FILE"

gunzip -c "$FILE" | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d casino_db

echo "Restore complete. Consider restarting backend: docker compose -f docker-compose.prod.yml restart backend"
