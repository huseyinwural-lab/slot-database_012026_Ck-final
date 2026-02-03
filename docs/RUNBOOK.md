## RUNBOOK (Ops)

### 1) Sağlık Kontrolleri
- `GET /api/v1/healthz` → `{ "status": "ok" }`
- `GET /api/v1/readyz` → `{ status: "ready", dependencies: { database, redis } }`
  - DB check: **POSTGRES_URL** (yoksa DATABASE_URL/varsayılan)
  - Redis check: `REDIS_URL` yoksa `redis=skipped`, varsa ping edilir

### 2) DB Migrasyonları (Alembic)
1. `cd /app/backend`
2. `alembic upgrade head`
3. `alembic current`
4. (Opsiyonel) `psql "$POSTGRES_URL" -c "SELECT * FROM alembic_version;"`

### 3) İlk Owner Admin Oluşturma (Bootstrap)
Çalıştırmadan önce env:
- `BOOTSTRAP_ENABLED=true`
- `BOOTSTRAP_OWNER_EMAIL=admin@casino.com`
- `BOOTSTRAP_OWNER_PASSWORD=Admin123!`
- `BOOTSTRAP_OWNER_TENANT_ID=default_casino` (opsiyonel)

Komut:
- `python /app/backend/scripts/bootstrap_owner.py`

İşlem sonrası `BOOTSTRAP_ENABLED=false` yapın.

### 4) Log Kontrolleri
- Backend: `/var/log/supervisor/backend.out.log`, `/var/log/supervisor/backend.err.log`
- Frontend: `/var/log/supervisor/frontend.out.log`, `/var/log/supervisor/frontend.err.log`
- Örnek: `tail -n 200 /var/log/supervisor/backend.err.log`

### 5) Golden Path Smoke Test
- `cd /app/e2e`
- `npx playwright test tests/smoke-launch.spec.ts`
