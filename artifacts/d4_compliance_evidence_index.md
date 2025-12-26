# Compliance Evidence Index (D4-3)

**Scope:** Audit, Retention, KYC, RG.
**Standard:** Licensed Operation Readiness.

## 1. Immutable Audit Trail
- **Hardening:** DB Triggers preventing UPDATE/DELETE.
  - *Proof:* `backend/tests/test_audit_immutable.py` (PASS)
- **Integrity:** Hash Chaining (SHA256).
  - *Proof:* `/app/artifacts/audit_chain_verify.txt` (PASS)
- **Retention:** 90 Days Hot + Remote Archive.
  - *Proof:* `scripts/purge_audit_logs.py` logic.

## 2. Archival & Restore
- **Archive Process:** Daily signed JSONL export.
  - *Sample:* `/app/artifacts/audit_archive_sample/`
- **Restore Test:** Break-glass procedure verified.
  - *Log:* `/app/artifacts/d4_backup_restore_logs.txt`

## 3. Responsible Gaming (RG) & KYC
- **KYC Verification:** Admin action logged with mandatory reason.
- **Self-Exclusion:** Player action immutably logged.
- **Smoke Test Log:** `/app/artifacts/d4_kyc_rg_smoke.md`

## 4. Operational Controls
- **Secrets Management:** `/app/artifacts/d4_secrets_checklist.md`
- **Access Control:** RBAC enforced (Admin vs Tenant Admin).
