# Restore Drill (P3.2) - Full Restore Exercise

Goal: periodically prove that backups are **actually restorable**.

> Do this in a non-production environment first.

## Preconditions
- You have at least one recent backup file:
  - `backups/casino_db_YYYYMMDD_HHMMSS.sql.gz`
- You can afford downtime in the target environment.

## Steps

### 1) Verify backup integrity
- Ensure file exists and is non-empty.
- Optional: `gunzip -t <file>` to verify gzip integrity.

### 2) Stop write traffic
- Stop the stack (or at minimum the backend) to prevent writes during restore.

### 3) Restore
From repo root:

```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```

### 4) Restart backend

```bash
docker compose -f docker-compose.prod.yml restart backend
```

### 5) Validate
- Health:
  - `curl -fsS http://127.0.0.1:8001/api/health`
  - `curl -fsS http://127.0.0.1:8001/api/ready`
- Version:
  - `curl -fsS http://127.0.0.1:8001/api/version`
- Login sanity:
  - `POST /api/v1/auth/login` (use known admin creds)

### 6) Record outcomes
Log the drill in a simple changelog:
- Date/time
- Backup filename
- Restore duration
- Any issues encountered
- Next actions

## Suggested frequency
- Staging: monthly
- Production: quarterly (or after major schema changes)


---

## Proof Template (copy/paste)

After each drill, create a proof file:
- `docs/ops/restore_drill_proof/YYYY-MM-DD.md`

Template is provided:
- `docs/ops/restore_drill_proof/YYYY-MM-DD.md`

Minimum proof requirements:
- date/time + environment
- backup artifact name
- restore command output
- validation outputs:
  - `GET /api/ready` (200)
  - `GET /api/version` (expected)
  - basic DB sanity (tenant count, admin exists, migrations head)
