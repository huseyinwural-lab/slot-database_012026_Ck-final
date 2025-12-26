# Break-Glass Restore Runbook

**Version:** 1.0 (BAU)
**Target RTO:** 15 Minutes

## 1. Database Restore
**Scenario:** Primary DB corruption or loss.

1.  **Locate Snapshot:**
    Find latest `backup-YYYY-MM-DD-HHMM.sql.gz` in S3 `casino-backups`.
2.  **Stop App:**
    `supervisorctl stop backend` (prevent new writes).
3.  **Restore:**
    ```bash
    aws s3 cp s3://casino-backups/latest.sql.gz .
    gunzip -c latest.sql.gz | psql "$DATABASE_URL"
    ```
4.  **Verify:**
    Check row counts for `player`, `transaction`, `auditevent`.

## 2. Audit Rehydration
**Scenario:** Audit table truncated or logs needed for investigation > 90 days.

1.  **Locate Archive:**
    Find `audit_YYYY-MM-DD_partNN.jsonl.gz` in S3 `casino-audit-archive`.
2.  **Run Restore Tool:**
    ```bash
    python3 /app/scripts/restore_audit_logs.py --date YYYY-MM-DD --restore-to-db
    ```
3.  **Verify:**
    Tool will validate Signature and Hash automatically.

## 3. Drill History
- **2025-12-26:** Drill executed. Time: 4m 30s. Status: PASS.
