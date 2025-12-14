#!/usr/bin/env sh
set -e

cd /app

ENV_NAME="${ENV:-dev}"

# Run migrations before starting the app (safe: no event loop running yet)
if [ "$ENV_NAME" = "prod" ] || [ "$ENV_NAME" = "staging" ]; then
  echo "[start_prod] Running alembic migrations (ENV=$ENV_NAME)"
  alembic upgrade head

  echo "[start_prod] Running one-shot owner bootstrap (if env vars present)"
  python /app/scripts/bootstrap_owner.py || true
else
  echo "[start_prod] Skipping migrations/bootstrap (ENV=$ENV_NAME)"
fi

echo "[start_prod] Starting uvicorn"
exec uvicorn server:app --host 0.0.0.0 --port 8001
