# Production Deployment Guide (Single VM + Docker Compose)

Target assumption:
- **Single Ubuntu VM (22.04 / 24.04)**
- **Docker Engine + Docker Compose v2**
- External reverse proxy (**Nginx or Traefik**) with **Let's Encrypt** TLS (TLS terminates at the external proxy; upstream traffic to the UI containers is plain HTTP)
- Two separate origins:
  - Admin UI: `https://admin.domain.tld`
  - Player UI: `https://player.domain.tld`

This document is intended to be a **single, end-to-end runbook**: a new operator should be able to bring the system up from zero.

---

## 1) Prerequisites (P1-DEPLOY-001)

### OS
- Ubuntu 22.04 LTS or 24.04 LTS

### Docker
Recommended minimums:
- Docker Engine: 24+ (CI uses newer versions; any modern Docker should work)
- Docker Compose plugin (v2): 2.20+

Verify:
```bash
docker version
docker compose version
```

### DNS
Create DNS records pointing to the VM:
- `admin.domain.tld` -> VM public IP
- `player.domain.tld` -> VM public IP

### TLS / Reverse proxy
Choose one:
- Nginx + Certbot (HTTP-01)
- Traefik with ACME (Let's Encrypt)

---

## 2) Repo layout & ports (P1-DEPLOY-001)

High-level map:
- `backend` (FastAPI) listens on **8001** (container port 8001, host publish 8001 in prod compose)
- `frontend-admin` serves the admin UI on **3000** (container port 80, host publish 3000)
- `frontend-player` serves the player UI on **3001** (container port 80, host publish 3001)
- `postgres` internal 5432 (persisted via docker volume)

Important routing model:
- Browsers call same-origin API paths:
  - `https://admin.domain.tld/api/v1/...`
  - `https://player.domain.tld/api/v1/...`
- The UI containers' internal Nginx proxies `location /api/` -> `proxy_pass http://backend:8001;` (Docker network).
- The **external** reverse proxy should forward `location /api/` to the UI container (not directly to backend), to preserve same-origin.
- Path handling rule: keep `/api/v1/...` intact (avoid trailing-slash rewrite mistakes).

---

## 3) First-time setup (P1-DEPLOY-001)

### 3.1 Environment files
Create env files (do not commit):
- Root: `/.env` (used by docker compose)
- Backend: `/backend/.env` (only if you run backend outside compose; optional)
- Frontend templates are build args in prod compose; you typically only need root `/.env`.

Templates are provided:
- `/.env.example`
- `/backend/.env.example`
- `/frontend/.env.example`
- `/frontend-player/.env.example`

### 3.2 Required values (production)
At minimum set in `/.env`:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `JWT_SECRET`
- `CORS_ORIGINS`

Recommended optional:
- `LOG_LEVEL=INFO`
- `LOG_FORMAT=auto` (prod/staging default: json, dev default: plain)
- `DB_POOL_SIZE=5`
- `DB_MAX_OVERFLOW=10`

### 3.3 Env checklist + secure value generation (P1-DEPLOY-003)

| Variable | Required | How to generate / example |
|---|---:|---|
| `JWT_SECRET` | ✅ | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | ✅ | `openssl rand -base64 24` (store safely) |
| `CORS_ORIGINS` | ✅ | `https://admin.domain.tld,https://player.domain.tld` |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://postgres:<POSTGRES_PASSWORD>@postgres:5432/casino_db` |

⚠️ **No wildcard in production**: `CORS_ORIGINS` must be an allowlist.

### 3.4 Bootstrap (one-shot) rule (P1-DEPLOY-003)

- Production rule: `BOOTSTRAP_ENABLED=false` by default.
- Only enable bootstrap for first install / controlled one-shot user creation.

If you set `BOOTSTRAP_ENABLED=true`, you must also set:
- `BOOTSTRAP_OWNER_EMAIL`
- `BOOTSTRAP_OWNER_PASSWORD`

After first successful login, set `BOOTSTRAP_ENABLED=false` again and redeploy.

---

## 4) Build & start (Docker Compose)

From repo root:
```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

docker compose -f docker-compose.prod.yml ps
```

---

## 5) Migrations

Migrations run on backend container startup.

Check:
```bash
docker compose -f docker-compose.prod.yml logs --no-color --tail=200 backend
```

---

## 6) Reverse proxy

Copy-paste examples:
- Nginx: `docs/reverse-proxy/nginx.example.conf`
- (Optional) Traefik: `docs/reverse-proxy/traefik.example.yml`

### WebSocket note (optional)
WebSocket is not required today. If you add WS later, ensure the reverse proxy includes:
- `Upgrade` / `Connection` headers
- sane read/write timeouts

---

## 7) Smoke test (2 minutes) (P1-DEPLOY-005)

### 7.1 Containers
```bash
docker compose -f docker-compose.prod.yml ps
```

### 7.2 Backend health
```bash
curl -fsS http://127.0.0.1:8001/api/health
curl -fsS http://127.0.0.1:8001/api/ready
# (optional) provide your own correlation ID
curl -fsS -H 'X-Request-ID: ABCdef12_-' http://127.0.0.1:8001/api/health -D - | head
```

### 7.3 Login sanity (curl)
You can validate auth directly (replace values):
```bash
API_BASE=http://127.0.0.1:8001
curl -sS -o /tmp/login.json -w "%{http_code}" \
  -X POST "${API_BASE}/api/v1/auth/login" \
  -H 'content-type: application/json' \
  --data '{"email":"admin@casino.com","password":"Admin123!"}'
cat /tmp/login.json
```

### 7.4 Reverse proxy check
From a browser:
- Open `https://admin.domain.tld/login`
- Confirm login works.
- In DevTools Network, requests should go to:
  - `https://admin.domain.tld/api/...` (same origin)
  - NOT directly to `:8001`

---

## 8) Logs

In `ENV=prod|staging`, logs are JSON by default (`LOG_FORMAT=auto`).
Each response includes `X-Request-ID` for correlation.

```bash
docker compose -f docker-compose.prod.yml logs --no-color --tail=300

docker compose -f docker-compose.prod.yml logs --no-color --tail=300 backend
```

---

## 9) Backup / Restore / Rollback (P1-DEPLOY-004)

## 9.1) Audit retention
See: `docs/ops/audit_retention.md` (90-day retention + purge script)

Primary doc:
- `docs/ops/backup.md`

Scripts (optional convenience):
- `./scripts/backup_postgres.sh`
- `./scripts/restore_postgres.sh <backup.sql.gz>`

Quick backup:
```bash
./scripts/backup_postgres.sh
```

Quick restore:
```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```

Rollback guideline:
- Prefer versioned image tags.
- Roll back by re-deploying the previous known-good image tag.
- For data corruption: restore DB from backup + redeploy previous image.
