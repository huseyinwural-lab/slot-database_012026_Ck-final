# Restore Drill Proof — YYYY-MM-DD

## Context

> Redaction required: Do not commit secrets. Mask tokens/passwords/keys and any credential-bearing URLs.
> Use `***` for sensitive values.

- Environment: staging / production / prod-compose
- Operator: <name>
- Backup Artifact:
  - Local: /var/lib/casino/backups/<backup_id>.dump
  - or S3: s3://<bucket>/<path>/<backup_id>.dump
- Target DB: <host:port/dbname>
- App Version expected: <e.g. 0.1.0>

## Pre-restore
- Maintenance enabled: yes/no
- Pre-restore snapshot/backup taken: yes/no (details)

## Restore Execution

Command:
```bash
./scripts/restore_postgres.sh ...
```

Output (tail):
```text
<paste output>
```

## Backend checks

### /api/health
Bash:
```bash
curl -i <URL>/api/health
```

Text:
```text
<paste output>
```

### /api/ready
Bash:
```bash
curl -i <URL>/api/ready
```

Text:
```text
<paste output>
```

### /api/version
Bash:
```bash
curl -s <URL>/api/version
```

Json:
```json
{ "service": "backend", "version": "<expected>", "git_sha": "____", "build_time": "____" }
```

### Auth / Capabilities
Bash:
```bash
curl -s <URL>/api/v1/tenants/capabilities -H "Authorization: Bearer ***"
```

Json:
```json
{ "is_owner": true }
```

## DB Sanity

### Alembic head/current
Bash:
```bash
alembic current
```

Text:
```text
<paste output>
```

### Basic counts
Bash:
```bash
psql "$DATABASE_URL" -c "select count(*) from tenants;"
psql "$DATABASE_URL" -c "select count(*) from admin_users;"
```

Text:
```text
<paste output>
```

## UI Smoke (Owner)
- Result: PASS/FAIL
- Notes: <any anomalies>

## Conclusion
- Restore drill result: PASS/FAIL
- Follow-ups: <list>
