#!/usr/bin/env sh
set -e

# Force unbuffered output for better logs
export PYTHONUNBUFFERED=1

cd /app

ENV_NAME="${ENV:-dev}"

echo "[start_prod] $(date -Iseconds) Starting up..."
echo "[start_prod] ENV=$ENV_NAME"


# Build metadata (safe to log)
echo "[start_prod] APP_VERSION=${APP_VERSION:-unknown}"
echo "[start_prod] GIT_SHA=${GIT_SHA:-unknown}"
echo "[start_prod] BUILD_TIME=${BUILD_TIME:-unknown}"

# Helper function for retrying commands
retry_cmd() {
    cmd="$@"
    n=0
    max=10
    delay=2
    while [ $n -lt $max ]; do
        if $cmd; then
            return 0
        else
            n=$((n+1))
            echo "[start_prod] Command '$cmd' failed. Attempt $n/$max. Retrying in ${delay}s..."
            sleep $delay
        fi
    done
    echo "[start_prod] Command '$cmd' failed after $max attempts."
    return 1
}

# Run migrations before starting the app
if [ "$ENV_NAME" = "prod" ] || [ "$ENV_NAME" = "staging" ]; then
  echo "[start_prod] $(date -Iseconds) Waiting for Postgres readiness (ENV=$ENV_NAME)"

  python - <<'PY'
import os
import time
import psycopg2

dsn = os.getenv("SYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
if not dsn:
    raise SystemExit("[start_prod] FATAL: Missing SYNC_DATABASE_URL/DATABASE_URL")

# Convert async DSN to sync DSN if needed
if "+asyncpg" in dsn:
    dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")

for i in range(60):
    try:
        psycopg2.connect(dsn).close()
        print("[start_prod] Postgres ready")
        break
    except Exception as e:
        print(f"[start_prod] Waiting for Postgres... ({i+1}/60) {e}")
        time.sleep(1)
else:
    raise SystemExit("[start_prod] Postgres did not become ready")
PY

  echo "[start_prod] $(date -Iseconds) Running alembic migrations (ENV=$ENV_NAME)"

  # Retry alembic upgrade to handle DB warmup race conditions
  if retry_cmd alembic upgrade head; then
      echo "[start_prod] $(date -Iseconds) Migrations applied successfully."
  else
      echo "[start_prod] $(date -Iseconds) ERROR: Migrations failed. Container will exit."
      exit 1
  fi

  echo "[start_prod] $(date -Iseconds) Running one-shot owner bootstrap (if env vars present)"
  if python /app/scripts/bootstrap_owner.py; then
      echo "[start_prod] $(date -Iseconds) Bootstrap completed or skipped."
  else
      echo "[start_prod] $(date -Iseconds) ERROR: Bootstrap script failed."
      exit 1
  fi
else
  echo "[start_prod] Skipping migrations/bootstrap (ENV=$ENV_NAME)"
fi

echo "[start_prod] $(date -Iseconds) Starting uvicorn"
exec uvicorn server:app --host 0.0.0.0 --port 8001
