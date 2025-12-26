# Go-Live Cutover Runbook & RC Sign-off

## 1. RC Sign-off Criteria (Met)
- **E2E (Money Loop):** PASS (Determinisitc via polling).
- **Backend Regression:** PASS (8/8 tests, covers ledger invariants).
- **Router/API:** Verified `payouts` router is active.
- **Ledger Logic:** Verified balance deduction on payout.
- **Artifacts:** Validated and hashed in `/app/artifacts/rc-proof/`.

## 2. Go-Live Cutover Runbook (T-0 Execution)

### A) Pre-Cutover (T-60 -> T-0)
1.  **Release Freeze:** 
    - Main branch locked.
    - RC Tag/Commit SHA verified.
2.  **Prod Config Verification:**
    - PSP Keys (Stripe/Adyen Live)
    - Webhook Secrets
    - DB URL & Trusted Proxies
    - `BOOTSTRAP_ENABLED=false`
3.  **DB Backup:**
    - Snapshot taken (Restore tested).
4.  **Migration Check:**
    - Dry-run `alembic upgrade head` on prod copy if possible.

### B) Cutover (T-0)
1.  **Maintenance Mode:**
    - Enable Maintenance Page / Block Ingress.
2.  **Deploy:**
    - Pull Docker Images.
    - `docker-compose up -d` (or k8s apply).
3.  **Migrations:**
    - Run `alembic upgrade head`.
4.  **Health Check:**
    - Verify `/api/health`.
    - Check Admin Login.
### Tools & Scripts
- **Config Verification:** `python3 scripts/verify_prod_env.py`
- **Backup Drill:** `bash scripts/db_restore_drill.sh`
- **Smoke Test:** `bash scripts/go_live_smoke.sh`
    - Check Dashboard Load.
    - Open Traffic.

### C) Post-Cutover (T+0 -> T+30)
1.  **Canary Smoke Test:**
    - Real-money Deposit ($10).
    - Real-money Withdraw ($10).
    - **Report Template:** Use `docs/ops/canary_report_template.md` for structured sign-off.
2.  **Ledger Check:**
    - Verify `held` -> `0` and `available` reduced correctly.
3.  **Webhook Watch:**
    - Tail logs for `Signature Verified` events.
4.  **Error Budget:**
    - Monitor Sentry/Logs for 5xx spikes.

## 3. Rollback Plan
**Triggers:**
- Payout Failure Rate > 15%.
- Critical Security Incident.
- Ledger Invariant Violation.

**Steps:**
1.  Enable Maintenance Mode.
2.  Revert to previous Docker Tag / Commit.
3.  Restore DB Snapshot (if data corruption suspect) OR Rollback Migration (if safe).
4.  Verify Login & Read-Only endpoints.
5.  Re-open Traffic.
