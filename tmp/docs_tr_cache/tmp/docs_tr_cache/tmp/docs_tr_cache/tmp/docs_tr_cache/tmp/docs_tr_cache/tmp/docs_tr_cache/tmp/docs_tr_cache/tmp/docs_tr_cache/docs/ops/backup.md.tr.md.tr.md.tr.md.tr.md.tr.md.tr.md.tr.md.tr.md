# Backup / Restore / Rollback (Production Ops)

Target assumption: Single VM (Ubuntu) + Docker Compose + Postgres container.

> If you use a managed Postgres (RDS/CloudSQL), prefer provider snapshots + PITR.

## 1) Backup (daily)

### 1.1 One-shot backup (recommended baseline)
From repo root:

```bash
./scripts/backup_postgres.sh
```

Optional retention cleanup (example: keep 14 days):

```bash
RETENTION_DAYS=14 ./scripts/backup_postgres.sh
```

### 1.2 Retention (simple)
Keep last 14 days:

```bash
find backups -type f -name 'casino_db_*.sql.gz' -mtime +14 -delete
```

### 1.3 VM/Compose (Cron) "ready-to-use" example
We ship an example cron file:
- `docs/ops/cron/casino-backup.example`

Install (on VM):
```bash
sudo mkdir -p /var/log/casino /var/lib/casino/backups
sudo cp docs/ops/cron/casino-backup.example /etc/cron.d/casino-backup
sudo chmod 0644 /etc/cron.d/casino-backup
sudo systemctl restart cron || sudo service cron restart
```

Notes:
- overlap prevention: `flock -n /var/lock/casino-backup.lock`
- logs: `/var/log/casino/backup.log`
- backups: `/var/lib/casino/backups`

Test run:
```bash
sudo -u root /bin/bash -lc 'cd /opt/casino && BACKUP_DIR=/var/lib/casino/backups RETENTION_DAYS=14 ./scripts/backup_postgres.sh'
```

## 1.4 Kubernetes CronJob (example)
We ship a "minimal edits" example:
- `k8s/cronjob-backup.yaml`

It supports:
- PVC-backed backups (active example)
- S3/object storage (alternative commented block)

Key settings (recommended):
- `concurrencyPolicy: Forbid` (no overlaps)
- `backoffLimit: 2`

Install:
```bash
kubectl apply -f k8s/cronjob-backup.yaml
```

You must create:
- Secret: `casino-db-backup` (DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD)
- PVC: `casino-backups-pvc` (or edit claim name)

## 2) Restore

> WARNING: restore overwrites data. Always confirm you target the correct DB.

```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```

## 2.1 Kubernetes restore note
If you run Postgres in Kubernetes:
- Prefer platform snapshots / managed DB PITR where possible.
- If you rely on logical backups (pg_dump), restore using a Job (psql) that targets the DB service.

(We provide a K8s backup CronJob example in `k8s/cronjob-backup.yaml`; you can mirror it into a restore Job.)

After restore:
- Restart backend (to clear any in-memory state):
  - `docker compose -f docker-compose.prod.yml restart backend`
- Validate:
  - `curl -fsS https://admin.domain.tld/api/health`

## 3) Rollback

### 3.1 App-only rollback (no DB restore)
If you tag/push images (recommended), rollback is:
- set compose image tags back to the previous known-good version
- `docker compose -f docker-compose.prod.yml up -d`

### 3.2 Full rollback (app + DB)
- Stop stack:
  - `docker compose -f docker-compose.prod.yml down`
- Restore DB from backup
- Start stack:
  - `docker compose -f docker-compose.prod.yml up -d`

## 4) "DB bozulursa nasıl dönerim?" hızlı cevap
1) Stack'i down al
2) Son sağlam backup'ı restore et
3) Önceki image tag'e dön
4) Health + login curl sanity ile doğrula
