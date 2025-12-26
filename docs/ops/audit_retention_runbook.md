# Audit Retention & Archival Runbook

## Overview
This runbook defines the procedures for maintaining the "Immutable Audit" system, including daily archiving, retention purging, and verifying integrity chains.

**Role Required:** Platform Owner / DevOps

## 1. Daily Archive Job
**Frequency:** Daily at 02:00 UTC
**Script:** `/app/scripts/audit_archive_export.py`

### Execution
```bash
# Export yesterday's logs
python3 /app/scripts/audit_archive_export.py --date $(date -d "yesterday" +%Y-%m-%d)
```

### Verification
1. Check that `manifest.json` and `manifest.sig` exist next to `.jsonl.gz`.
2. Verify signature using the `AUDIT_EXPORT_SECRET`.

## 2. Retention Purge
**Frequency:** Monthly
**Policy:** Keep 90 days in "Hot" DB, archive older.

### Execution
*Currently manual, to be automated in Task D2.*
```sql
DELETE FROM auditevent WHERE timestamp < NOW() - INTERVAL '90 days';
```
**Note:** This requires temporarily disabling the `prevent_audit_delete` trigger.
```sql
DROP TRIGGER prevent_audit_delete;
-- DELETE ...
-- Re-create trigger
```

## 3. Chain Verification (Integrity Check)
To verify that no rows have been deleted or tampered with in the active DB.

### Script
*Upcoming in Task D1.7*

## 4. Emergency: Exporting Evidence for Legal
If a regulator requests specific logs:
1. Use the Admin UI `/audit` page with filters.
2. Click "Export CSV".
3. Provide the CSV + the corresponding Daily Archive manifest if the logs are older than 90 days.
