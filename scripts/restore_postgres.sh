#!/usr/bin/env bash
set -euo pipefail

# Restore Postgres DB from a .sql.gz backup file.
#
# Usage:
#   ./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
#
# Optional env:
#   DB_NAME=casino_db DB_USER=postgres ./scripts/restore_postgres.sh <file>
#   COMPOSE_FILE=/path/to/docker-compose.prod.yml ./scripts/restore_postgres.sh <file>
#
# WARNING: This overwrites data in the target database.

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.sql.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${REPO_ROOT}/docker-compose.prod.yml}"
DB_NAME="${DB_NAME:-casino_db}"
DB_USER="${DB_USER:-postgres}"

read -r -p "This will RESTORE and overwrite DB '${DB_NAME}'. Type 'RESTORE' to continue: " CONFIRM
if [[ "${CONFIRM}" != "RESTORE" ]]; then
  echo "Aborted."
  exit 1
fi

echo "Restoring ${BACKUP_FILE} -> ${DB_NAME} ..."

gunzip -c "${BACKUP_FILE}" | docker compose -f "${COMPOSE_FILE}" exec -T postgres \
  psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Restore complete."
echo "Recommended next steps:"
echo "- docker compose -f ${COMPOSE_FILE} restart backend"
echo "- curl -fsS http://127.0.0.1:8001/api/ready"
