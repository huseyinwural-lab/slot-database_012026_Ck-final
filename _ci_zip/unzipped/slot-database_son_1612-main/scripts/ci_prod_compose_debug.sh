#!/usr/bin/env bash
# Intentionally NOT using `set -e` to guarantee artifact output even when docker/compose is unhealthy.
set -u
set -o pipefail

COMPOSE_FILE="${1:-docker-compose.prod.yml}"
OUT_DIR="${2:-ci_artifacts}"

mkdir -p "$OUT_DIR"

# Capture compose ps
{
  echo "=== docker compose ps ==="
  echo "compose_file=$COMPOSE_FILE"
  echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  docker compose -f "$COMPOSE_FILE" ps || true
} > "$OUT_DIR/compose_ps.txt"

# Capture tail logs
{
  echo "=== docker compose logs (tail 400) ==="
  docker compose -f "$COMPOSE_FILE" logs --no-color --tail=400 || true
} > "$OUT_DIR/compose_logs_tail.txt"

# Optional: inspect containers (best-effort)
SERVICES=(postgres backend frontend-admin frontend-player)
for svc in "${SERVICES[@]}"; do
  cid=$(docker compose -f "$COMPOSE_FILE" ps -q "$svc" 2>/dev/null || true)
  if [ -n "$cid" ]; then
    docker inspect "$cid" > "$OUT_DIR/inspect_${svc}.json" || true
  fi
done

# Mask secrets in-place (preserve line structure)
python3 - <<PY
import re
from pathlib import Path

out_dir = Path("$OUT_DIR")
files = [out_dir / "compose_ps.txt", out_dir / "compose_logs_tail.txt"]

# Key=VALUE masking (keeps key and '=' intact)
kv_patterns = [
    re.compile(r"(?i)\b(PASSWORD|TOKEN|JWT|KEY|SECRET)\b\s*[:=]\s*([^\s,;]+)"),
]

# DATABASE_URL masking: postgresql://user:pass@host/db -> user:****@
dburl_patterns = [
    re.compile(r"(?i)(postgres(?:ql)?\+?\w*://[^:\s/]+:)([^@\s/]+)(@)")
]

for p in files:
    if not p.exists():
        continue
    text = p.read_text(errors="ignore")

    for pat in kv_patterns:
        text = pat.sub(lambda m: f"{m.group(1)}=*****", text)

    for pat in dburl_patterns:
        text = pat.sub(lambda m: f"{m.group(1)}*****{m.group(3)}", text)

    p.write_text(text)
PY

echo "Artifacts written to: $OUT_DIR"