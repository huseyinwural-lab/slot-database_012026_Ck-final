# Release Ops Decision Tree (P3)

Goal: At 03:00, an operator can choose the correct action with minimal ambiguity.

This doc consolidates:
- Rollback (`docs/ops/rollback.md`)
- Migrations strategy (`docs/ops/migrations.md`)
- Backup/restore (`docs/ops/backup.md`)
- Version/health signals (`docs/ops/release_build_metadata.md`, `docs/ops/observability.md`)

---

## 0) Always collect signals (2 minutes)

### Backend readiness
- Compose:
  ```bash
  curl -fsS http://127.0.0.1:8001/api/ready
  ```
- K8s:
  ```bash
  kubectl get pods
  kubectl logs deploy/backend --tail=200
  ```

### Version
- Compose:
  ```bash
  curl -fsS http://127.0.0.1:8001/api/version
  ```
- Public (behind admin domain):
  ```bash
  curl -fsS https://admin.domain.tld/api/version
  ```

### Quick smoke
- Login as owner admin
- Open: Tenants list
- Settings → Versions

---

## 1) Decision Tree

### A) Deploy sonrası **/api/ready FAIL** (DB/migration/startup)

**Symptoms**:
- `/api/ready` != 200
- backend logs show DB connection errors or migration errors

**Action**:
1) If migration failure is fixable quickly: **hotfix-forward** (preferred)
   - e.g., fix migration, release `vX.Y.Z+1-<gitsha>` and redeploy
2) If time-critical and DB is now in unknown state:
   - restore DB from last known-good backup
   - redeploy previous known-good image tag

**Compose commands**:
- Restore (see `docs/ops/backup.md`):
  ```bash
  ./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
  docker compose -f docker-compose.prod.yml restart backend
  ```
- Rollback app images (see `docs/ops/rollback.md`):
  ```bash
  # edit docker-compose.prod.yml pinned image tags
  docker compose -f docker-compose.prod.yml up -d
  ```

**K8s commands**:
- Roll back deployment:
  ```bash
  kubectl rollout undo deploy/backend
  kubectl rollout status deploy/backend
  ```
- If DB restore needed: follow your platform DB restore (snapshot/PITR or restore job).

**Verify**:
- `/api/ready` → 200
- `/api/version` → expected
- owner login works

---

### B) UI bozuk ama backend sağlam (ready OK, API OK)

**Symptoms**:
- `/api/ready` = 200
- `/api/version` = expected
- Admin UI errors (blank screen, JS error, missing assets)

**Action**:
- Roll back **only UI** (fastest) to previous known-good frontend-admin image tag.

**Compose**:
```bash
# pin previous image for frontend-admin only
# docker compose -f docker-compose.prod.yml up -d
```

**K8s**:
```bash
kubectl set image deploy/frontend-admin frontend-admin=registry.example.com/casino/frontend-admin:vX.Y.Z-<gitsha>
kubectl rollout status deploy/frontend-admin
```

**Verify**:
- Login
- Settings → Versions
- Tenants page loads

---

### C) DB uyumsuzluğu şüphesi (rollback sonrası 500/404 gariplikleri)

**Symptoms**:
- Rollback yaptın ama bazı endpoint’ler 500/404
- Loglarda "no such column/table" / schema mismatch

**Action**:
1) Prefer **hotfix-forward** to restore compatibility quickly.
2) Eğer mümkün değilse: **restore DB + redeploy previous tag**.

**Verify checklist**:
- `/api/ready` 200
- `/api/version` expected
- Login success
- Critical pages: Dashboard, Tenants, Settings

---

## 2) Minimal release smoke checklist (PASS/FAIL)

- [ ] `/api/health` 200
- [ ] `/api/ready` 200
- [ ] `/api/version` returns expected version
- [ ] Owner login OK
- [ ] Tenants list OK
- [ ] Settings → Versions OK
- [ ] Logout OK
