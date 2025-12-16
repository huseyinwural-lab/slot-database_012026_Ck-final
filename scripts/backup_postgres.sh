#!/usr/bin/env bash
set -euo pipefail

# Backup postgres running in docker-compose.prod.yml
# Output: ./backups/casino_db_<UTC_TIMESTAMP>.sql.gz

cd "$(dirname "$0")/.."

mkdir -p backups
TS=$(date -u +%Y%m%d_%H%M%S)
FILE="backups/casino_db_${TS}.sql.gz"

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres -d casino_db \
  | gzip > "$FILE"

echo "Backup written: $FILE"
