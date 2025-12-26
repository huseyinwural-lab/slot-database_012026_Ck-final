# Sprint D - Task 1: Immutable Audit + Retention (P0-OPS)

## 🛡️ Goal
Secure the audit trail against tampering and data loss, ensuring "write-once" integrity and automated archival for compliance.

## ✅ Scope & Deliverables

### 1. DB Hardening ("Write-Once")
- **Triggers:** `prevent_audit_update` and `prevent_audit_delete` triggers applied to `auditevent` table.
- **Verification:** `tests/test_audit_immutable.py` confirms UPDATE/DELETE operations are blocked by DB.

### 2. Retention Policy
- **Config:** `AUDIT_RETENTION_DAYS` (default 730) added to `config.py`.
- **Policy:** Keep 90 days hot, archive daily.

### 3. Hash Chaining (Tamper-Evident)
- **Schema:** Added `row_hash`, `prev_row_hash`, `chain_id`, `sequence` to `auditevent`.
- **Logic:** `AuditLogger` computes SHA256 hash of (prev_hash + canonical_json(event)).
- **Verification:** `scripts/verify_audit_chain.py` validates the integrity of the chain.

### 4. Archive Pipeline
- **Script:** `/app/scripts/audit_archive_export.py`
- **Output:** Daily `.jsonl.gz` + `manifest.json` + `manifest.sig` (HMAC signed).
- **Security:** Export action is audited (`AUDIT_EXPORT` event).

### 5. Ops Runbook
- **Location:** `/app/docs/ops/audit_retention_runbook.md`
- **Contents:** Daily archive procedure, retention purge steps, chain verification.

### 6. Evidence
- **Tests:** All passed (`test_audit_hash_chain.py`, `test_audit_immutable.py`, `test_audit_archive_export.py`).
- **Chain Verification:** `/app/artifacts/audit_chain_verify.txt` (SUCCESS).
- **Sample Archive:** `/app/artifacts/audit_archive_sample/` (Contains signed export).

## 🚀 Next Steps (Task D2)
- **Automated Purge:** Implement the cron job for retention deletion (currently manual in runbook).
- **Remote Storage:** Push archives to S3/MinIO (currently local FS).

## ✅ GO/NO-GO
**GO** - System is immutable, chained, and ready for licensed audit operations.
