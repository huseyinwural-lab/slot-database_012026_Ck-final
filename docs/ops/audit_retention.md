# Audit Log Retention (90 days)

This project stores canonical audit events in the `AuditEvent` SQLModel (SQLite: `auditevent`).

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
python scripts/purge_audit_events.py --days 90
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
