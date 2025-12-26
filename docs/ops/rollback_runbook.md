# Rollback Runbook

**Version:** 1.0 (Final)

## Triggers (When to Rollback)
1. **Critical Failure:** >5% 5xx Error Rate sustained for 10 mins.
2. **Data Integrity:** Audit Chain Verification Fails (`verify_audit_chain.py` returns error).
3. **Financial Risk:** Double-spend detected or massive Recon Mismatch.

## Strategy: Forward Fix vs. Rollback
- **Preferred:** Forward Fix (Hotfix) for code bugs.
- **Rollback:** For DB corruption or catastrophic config error.

## Procedure (Rollback)

### 1. Stop Traffic
- Enable Maintenance Mode.

### 2. Database Restore
*WARNING: Data lost since last backup will be lost unless WAL logs are replayed.*
1. Terminate DB connections.
2. Restore from Pre-Cutover Snapshot (see `d4_backup_restore_drill.md`).
3. Verify DB Health.

### 3. App Rollback
1. Revert Container Image tag to `previous-stable`.
2. Redeploy pods.

### 4. Verification
1. Run Smoke Test Suite (`scripts/d4_smoke_runner.py` adapted for prod).
2. Check `/api/v1/ops/health`.

### 5. Resume Traffic
- Disable Maintenance Mode.
- Notify stakeholders.
