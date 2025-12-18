# Restore Drill Proof - YYYY-MM-DD

> Copy this template to a date-stamped file:
> - `docs/ops/restore_drill_proof/2025-12-18.md`

## Metadata
- Date (UTC): YYYY-MM-DDTHH:MM:SSZ
- Environment: staging | prod | other
- App version (expected): vX.Y.Z-<gitsha>
- Operator: <name>

## Backup artifact
- Filename: backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
- Size: <bytes>
- Checksum (optional): <sha256>

## Restore command output
Command:
```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```

Output (paste):
```text
...
```

## Post-restore validation

### 1) Ready
```bash
curl -fsS -i http://127.0.0.1:8001/api/ready
```

Expected:
- HTTP 200
- body contains `status":"ready"`

Actual output:
```text
...
```

### 2) Version
```bash
curl -fsS -i http://127.0.0.1:8001/api/version
```

Expected:
- HTTP 200
- version/git_sha/build_time match deployment expectation

Actual output:
```text
...
```

### 3) DB sanity (examples)

Tenant count:
```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d casino_db -c 'select count(*) from tenant;'
```

Admin exists:
```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d casino_db -c "select email,is_platform_owner from adminuser where email='admin@casino.com';"
```

Migrations head (if prod/staging uses alembic):
```bash
docker compose -f docker-compose.prod.yml exec -T backend \
  alembic current
```

## Outcome
- Result: PASS | FAIL
- Restore duration: <minutes>
- Notes:
  - ...
