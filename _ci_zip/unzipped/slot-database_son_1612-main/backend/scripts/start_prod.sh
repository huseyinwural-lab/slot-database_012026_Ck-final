#!/usr/bin/env sh
set -e

# Force unbuffered output for better logs
export PYTHONUNBUFFERED=1

cd /app

ENV_NAME="${ENV:-dev}"

echo "[start_prod] $(date -Iseconds) Starting up..."
echo "[start_prod] ENV=$ENV_NAME"

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
  echo "[start_prod] $(date -Iseconds) Running alembic migrations (ENV=$ENV_NAME)"
  
  # Retry alembic upgrade to handle DB warmup race conditions
  if retry_cmd alembic upgrade head; then
      echo "[start_prod] $(date -Iseconds) Migrations applied successfully."
  else
      echo "[start_prod] $(date -Iseconds) ERROR: Migrations failed. Container will exit."
      exit 1
  fi

  echo "[start_prod] $(date -Iseconds) Running one-shot owner bootstrap (if env vars present)"
  # Bootstrap is also critical, but '|| true' was used before. 
  # Let's keep it safe but log explicitly.
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
