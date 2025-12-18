#!/usr/bin/env bash
set -euo pipefail

# Backup Postgres DB from docker-compose.prod.yml
#
# Usage:
#   ./scripts/backup_postgres.sh
#   BACKUP_DIR=backups DB_NAME=casino_db ./scripts/backup_postgres.sh
#   RETENTION_DAYS=14 ./scripts/backup_postgres.sh
#
# Assumptions:
# - Run from repo root (or any dir; script resolves repo root).
# - docker compose is available.
# - postgres service name is "postgres".

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${REPO_ROOT}/docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-${REPO_ROOT}/backups}"
DB_NAME="${DB_NAME:-casino_db}"
DB_USER="${DB_USER:-postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-}"

mkdir -p "${BACKUP_DIR}"
TS="$(date -u +%Y%m%d_%H%M%S)"
FILE="${BACKUP_DIR}/${DB_NAME}_${TS}.sql.gz"

# Dump + gzip on the host (keeps container clean)
docker compose -f "${COMPOSE_FILE}" exec -T postgres \
  pg_dump -U "${DB_USER}" -d "${DB_NAME}" \
  | gzip > "${FILE}"

echo "Backup written: ${FILE}"

# Optional retention cleanup
if [[ -n "${RETENTION_DAYS}" ]]; then
  find "${BACKUP_DIR}" -type f -name "${DB_NAME}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
  echo "Retention applied: deleted backups older than ${RETENTION_DAYS} days (if any)"
fi
