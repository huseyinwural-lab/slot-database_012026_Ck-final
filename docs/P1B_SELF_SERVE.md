# P1-B Self-Serve Proof Pack (External Postgres + Redis) — Go/No-Go Gate

## Purpose
Validate production-like readiness with **external Postgres** and **external Redis**:
- Migrations apply cleanly on real Postgres
- Service becomes **Ready (200)** only when **DB + Redis** are actually reachable
- If Redis is missing/unreachable, Ready is **503** (no traffic)

This document is designed for **URL-less evidence sharing** (mask secrets).

---

## Contract Summary

### Import-time (fail-fast) — presence/shape checks
When `ENV in {staging, prod}` **OR** `CI_STRICT=1`:
- `DATABASE_URL` unset → startup **FAIL**
- `DATABASE_URL` sqlite scheme → startup **FAIL**
- `REDIS_URL` unset → startup **FAIL**

### Runtime (Go/No-Go) — real connectivity checks
When `ENV in {staging, prod}` **OR** `CI_STRICT=1`:
- `GET /api/ready`
  - DB OK + Redis `PING` OK → **200**
  - Redis unreachable → **503**

---

## Evidence Masking Rules
When sharing logs:
- Replace credentials with `***`
- Acceptable masking examples:
  - `postgresql+asyncpg://user:PASS@host:5432/db` → `postgresql+asyncpg://user:***@host:5432/db`
  - `redis://:PASS@host:6379/0` → `redis://:***@host:6379/0`
- If needed, partially mask hostnames/IPs, but keep enough signal to diagnose (e.g. keep port and scheme).

---

## Step 1 — External Migration Gate (Postgres)

### Commands
```bash
cd /app/backend

export ENV=staging
export CI_STRICT=1
export DATABASE_URL='postgresql+asyncpg://...'
export REDIS_URL='redis://...'

alembic upgrade head
alembic current
```

### Pass Criteria
- `alembic upgrade head` exits **0**
- `alembic current` shows **head** revision

### Evidence to Share (masked)
- `alembic upgrade head` output
- `alembic current` output

---

## Step 2 — Runtime Ready Gate (DB + Redis)

### Start Service
Use the repo’s canonical entrypoint.

Examples:

**Dev/self-serve (direct uvicorn):**
```bash
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001
```

**Prod-like container entrypoint (runs migrations in staging/prod):**
```bash
/app/scripts/start_prod.sh
```

### Check Ready + Version
```bash
curl -sS -i http://localhost:8001/api/ready
curl -sS -i http://localhost:8001/api/version
```

### Pass Criteria
- `/api/ready` returns **200**
- Response indicates DB connected and Redis connected (field names may vary; in this repo `/api/ready` currently returns `dependencies.database|redis|migrations`)

### Evidence to Share (masked)
- Full response headers + body of `/api/ready`
- `/api/version` output
- Boot log lines for DB connection + Redis ping

---

## Step 3 — Negative Proof (Redis broken ⇒ Ready 503)

### Break Redis URL
```bash
export REDIS_URL='redis://:***@127.0.0.1:1/0'
# restart service if needed
```

### Check Ready
```bash
curl -sS -i http://localhost:8001/api/ready
```

### Pass Criteria
- `/api/ready` returns **503**
- Body indicates Redis unreachable

### Evidence to Share
- `/api/ready` response (masked)
- Relevant log lines showing Redis ping failure

---

## Optional Step 4 — Fail-fast runtime test (no listener)
This verifies strict mode exits quickly if Redis URL is missing.

```bash
cd /app/backend
export ENV=staging
export CI_STRICT=1
unset REDIS_URL
pytest -q tests/test_runtime_failfast_redis_uvicorn.py
```

Pass: test is green.

---

## Recommended Response Format for /api/ready
To reduce ambiguity, `/api/ready` should include machine-readable fields.

Example (recommended):
```json
{
  "status": "ok|fail",
  "checks": {
    "db": {"ok": true, "detail": "connected|unreachable"},
    "redis": {"ok": true, "detail": "connected|unreachable"}
  }
}
```

(Exact schema is not required for the gate, but strongly recommended.)

---

## Two small but critical improvements (recommended)

1) **Standardize `/api/ready` JSON**
Even if today’s `dependencies.redis=connected/unreachable` is sufficient, having a stable shape like `status + checks` makes CI/CD and on-call debugging much faster.

2) **Short readiness timeouts**
Keep DB/Redis checks bounded (e.g. ~0.5–2s). In allowlist/VPC/DNS failures, you want a fast **503** rather than a hanging probe.

---

## Result & Next Step
If Steps 1–3 are satisfied (and optionally Step 4), P1-B is considered **Go** from a deployment-readiness perspective.

Next (optional): standardize a one-page closure report template (“evidence checklist + outputs + timestamps”).

---

## Evidence Output Template (Audit Trail)

> Goal: provide a compact, reproducible evidence trail without leaking secrets.
> Paste outputs in this structure. Mask credentials and sensitive hosts as per rules above.

### Metadata
- Date (UTC): 2025-__-__T__ :__ :__Z
- Environment: staging | prod | ci
- Service version: $(curl -sS http://localhost:8001/api/version | head -c 200)
- Git SHA (if available): ________
- Runner/Host (masked): ________
- Operator: ________ (optional)

---

### Step 1 — External Migration Gate (Postgres)

**Command**
```bash
cd /app/backend
export ENV=staging
export CI_STRICT=1
export DATABASE_URL='postgresql+asyncpg://user:***@host:5432/db'
export REDIS_URL='redis://:***@host:6379/0'

alembic upgrade head
echo "EXIT_CODE=$?"
alembic current
echo "EXIT_CODE=$?"
```

**Exit Codes**
- alembic upgrade head: EXIT_CODE=0|non-0
- alembic current: EXIT_CODE=0|non-0

**Output (first/last lines)**
- upgrade head (first 10 lines):
  - ...
- upgrade head (last 10 lines):
  - ...
- current:
  - ...

---

### Step 2 — Runtime Ready Gate (DB + Redis)

**Command**
```bash
curl -sS -i http://localhost:8001/api/ready
echo "EXIT_CODE=$?"
curl -sS -i http://localhost:8001/api/version
echo "EXIT_CODE=$?"
```

**Expected**
- /api/ready: HTTP 200
- Response includes dependencies.database=connected, dependencies.redis=connected
- If present: dependencies.migrations=head (or equivalent)

**Output (full)**
- /api/ready:
  - ...
- /api/version:
  - ...

---

### Step 3 — Negative Proof (Redis broken => Ready 503)

**Command**
```bash
export REDIS_URL='redis://:***@127.0.0.1:1/0'
# restart service if required by your runtime
curl -sS -i http://localhost:8001/api/ready
echo "EXIT_CODE=$?"
```

**Expected**
- /api/ready: HTTP 503
- dependencies.redis=unreachable (or equivalent)

**Output (full)**
- /api/ready:
  - ...

---

### Optional Step 4 — Fail-fast (strict mode, no listener)

**Command**
```bash
cd /app/backend
export CI_STRICT=1
unset REDIS_URL
pytest -q backend/tests/test_runtime_failfast_redis_uvicorn.py
echo "EXIT_CODE=$?"
```

**Expected**
- EXIT_CODE=0

**Output**
- ...

---

## Implementation Notes (small but valuable)
- Always fill the “Service version” field — it closes the loop on “which build produced this evidence?”.
- Calling out `dependencies.migrations` in Step 2 helps catch migration drift at runtime.
- This template is artifact-friendly: you can store it as a CI artifact without secrets.
