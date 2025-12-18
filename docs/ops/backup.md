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

### 1.3 Cron example
Create `/etc/cron.d/casino-backup`:

```cron
# daily at 02:10 UTC
10 2 * * * ubuntu /bin/bash -lc 'cd /opt/casino && ./scripts/backup_postgres.sh' >> /var/log/casino-backup.log 2>&1
```

## 2) Restore

> WARNING: restore overwrites data. Always confirm you target the correct DB.

```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```

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
