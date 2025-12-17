# Audit Log Retention (90 days)

This project stores canonical audit events in the `AuditEvent` SQLModel.

## Environments / DB separation (SQLite vs Postgres)
- **Dev/local**: typically uses **SQLite** (`sqlite+aiosqlite:////app/backend/casino.db`).
- **Staging/prod**: expected to use **PostgreSQL** (via `DATABASE_URL`).

The purge script connects to **whatever DB is configured** in `backend/config.py` via `settings.database_url`.

### Table name
In this codebase the audit table name is **`auditevent`** (SQLModel default naming). The purge tool and SQL snippets assume this.

## Timestamp
- Audit `timestamp` is stored in **UTC**.
- Purge cutoff is computed in **UTC** and compared against the DB `timestamp` column.

## Goal
- Keep audit events for **90 days**
- Ensure queries (by time, tenant, action) remain fast
- Provide an operationally simple purge procedure

## Recommended Indexes
### SQLite
SQLite already benefits from the indexes created by migrations on:
- `timestamp`
- `tenant_id`
- `action`
- `actor_user_id`
- `request_id`
- `resource_type`
- `resource_id`

### PostgreSQL (staging/prod)
Create indexes for common access patterns:

```sql
-- time range scans
CREATE INDEX IF NOT EXISTS ix_audit_event_timestamp ON auditevent (timestamp DESC);

-- tenant + time
CREATE INDEX IF NOT EXISTS ix_audit_event_tenant_time ON auditevent (tenant_id, timestamp DESC);

-- action filters
CREATE INDEX IF NOT EXISTS ix_audit_event_action_time ON auditevent (action, timestamp DESC);

-- request correlation
CREATE INDEX IF NOT EXISTS ix_audit_event_request_id ON auditevent (request_id);
```

> If you rename the table in Postgres to `audit_event`, adjust the SQL accordingly.

## Purge Strategy
### Policy
- Delete events older than **90 days**.
- Run at least **daily** during low-traffic hours.

### Scripted purge (recommended)
Use `scripts/purge_audit_events.py`:

```bash
# Dry-run (no deletes) – prints JSON summary
python scripts/purge_audit_events.py --days 90 --dry-run

# Batch delete (default batch size is 5000)
python scripts/purge_audit_events.py --days 90 --batch-size 5000
```

### Running inside container (compose example)
If running via Docker Compose, execute inside the backend container:

```bash
docker compose exec backend python /app/scripts/purge_audit_events.py --days 90 --dry-run
```

### Cron example
Run at 03:15 every day:

```cron
15 3 * * * cd /opt/casino-admin && /usr/bin/python3 scripts/purge_audit_events.py --days 90 >> /var/log/casino-admin/audit_purge.log 2>&1
```

## Safety Notes
- Purge is **irreversible**.
- Keep DB backups (see `docs/ops/backup.md`).
- The purge script only deletes by `timestamp < cutoff`.

## Verification
After a purge:
- Query count of remaining rows (optional):

```sql
SELECT COUNT(*) FROM auditevent;
```

- Verify the latest audit events are still available via the API:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "<BASE_URL>/api/v1/audit/events?since_hours=24&limit=10"
```
