# Release Checklist (Staging / Production)

## 1) CI / Quality gates
- [ ] GitHub Actions: **Prod Compose Acceptance** workflow is GREEN
- [ ] Playwright E2E tests are PASS

## 2) Environment / Secrets
- [ ] `ENV=staging` or `ENV=prod` set correctly
- [ ] `JWT_SECRET` is strong (not default)
- [ ] `POSTGRES_PASSWORD` is strong
- [ ] `DATABASE_URL` correct and points to the intended Postgres
- [ ] `CORS_ORIGINS` is an allowlist (no `*` in prod/staging)
- [ ] `TRUSTED_PROXY_IPS` set to your external reverse proxy IP(s) if you want to trust `X-Forwarded-For`

## 3) Bootstrap rule
- [ ] `BOOTSTRAP_ENABLED=false` in steady-state production
- [ ] If bootstrap is needed, enable temporarily, create owner, then disable and redeploy

## 4) Deploy
- [ ] `docker compose -f docker-compose.prod.yml build`
- [ ] `docker compose -f docker-compose.prod.yml up -d`
- [ ] External reverse proxy routes:
  - `admin.domain.tld` -> admin UI container
  - `player.domain.tld` -> player UI container
  - `/api/*` forwarded to UI container (same-origin), not to backend directly

## 5) Post-deploy smoke tests
Run:
- [ ] `docker compose -f docker-compose.prod.yml ps`
- [ ] `curl -fsS http://127.0.0.1:8001/api/health`
- [ ] `curl -fsS http://127.0.0.1:8001/api/ready`
- [ ] Browser check: `https://admin.domain.tld` login works and Network shows `https://admin.domain.tld/api/v1/...`

## 6) Backup readiness
- [ ] Backup script tested: `./scripts/backup_postgres.sh`
- [ ] Restore steps understood: `docs/ops/backup.md`

## 7) Versioning / rollback recommendation
- [ ] Tag images/releases (or keep last known-good artifacts)
- [ ] Keep previous compose + env for rollback
