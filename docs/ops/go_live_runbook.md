# Go-Live Cutover Runbook & RC Sign-off

## Cutover Preconditions
**Do NOT start cutover unless these are met:**
*   **Release Pin:** Release SHA/Tag pinned and communicated.
*   **Access:** Prod access (DB, Registry, Deploy) verified for responsible owners.
*   **Artifacts:** RC Artifacts (`/app/artifacts/rc-proof/`) present and hashes verified.
*   **Rollback:** Plan and "Restore Point" (Snapshot) owner assigned.
*   **Canary:** Canary user/tenant ready with test amounts defined.
*   **Hypercare:** On-call rotation and alert channels active.

## War Room Protocol (Sprint 7 Cutover)
**Goal:** Single source of truth for GO/NO-GO decisions.

### Roles
*   **Incident Commander (IC):** Sole decision maker (GO/NO-GO/ROLLBACK).
*   **Deployer:** Executes deploy and smoke scripts.
*   **DB Owner:** Manages snapshots and migration monitoring.
*   **Payments Owner:** Validates Canary Money Loop & Ledger Invariants.
*   **Scribe:** Logs timeline, references, and decisions.

### Rules
1.  All steps follow the checklist. No skipping.
2.  **Canary FAIL = NO-GO** (No exceptions).
3.  If Rollback trigger observed, IC decides within 5 minutes.
4.  Log every step: PASS/FAIL + Timestamp.

### Timeline (Scribe Format)
*   **T-60:** Pre-flight Start/End.
*   **T-30:** Snapshot ID recorded.
*   **T-15:** Deploy Start/End.
*   **T-10:** Smoke PASS/FAIL.
*   **T-0:** Canary PASS/FAIL.
*   **T+15:** GO/NO-GO Decision.
*   **T+60:** First Hypercare Report.

## Communication Plan (Cutover Broadcast)
### Channels & Messages
1.  **Cutover Start:** "Cutover initiated. Maintenance window active. Updates every 15m."
2.  **Checkpoint Updates:**
    *   "Pre-flight PASS"
    *   "Backup PASS"
    *   "Deploy+Smoke PASS/FAIL"
    *   "Canary PASS/FAIL"
3.  **GO-LIVE Announcement:** "GO decision made. System live. Hypercare started."
4.  **Rollback (If needed):** "Rollback triggered. Reason: [X]. Restoration in progress."

### Update Cadence
*   **During Cutover:** Every 15m or at checkpoints.
*   **First 2 Hours:** Every 30m.
*   **2-24 Hours:** Hourly summary.

---

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
    - Check Dashboard Load.
    - Open Traffic.

### Tools & Scripts
- **Config Verification:** `python3 scripts/verify_prod_env.py`
- **Backup Drill:** `bash scripts/db_restore_drill.sh`
- **Smoke Test:** `bash scripts/go_live_smoke.sh`

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

## 4. Sprint 7 — Cutover Command Sheet (One-Pager)

### T-60 — Pre-flight
1.  **Release Pin:** Define `RELEASE_SHA` / Tag.
2.  **Prod Env Check:** `python3 scripts/verify_prod_env.py`
    *   *Acceptance:* Prod mode, CORS restricted, no test secrets (or waived via ticket).

### T-30 — Backup
1.  **DB Snapshot:** Execute via Cloud Provider or `pg_dump` (do NOT run restore drill in Prod).
2.  **Record:** Snapshot ID/Path + Timestamp + Checksum.

### T-15 — Deploy + Migration + Smoke
1.  **Deploy & Migrate:** `bash scripts/go_live_smoke.sh`
    *   *Acceptance:* Migrations OK, API Health 200, Login OK, Payouts Router reachable.

### T-0 — Canary Money Loop (GO Decision)
1.  **Execute:** `docs/ops/canary_report_template.md` steps.
    *   Deposit -> Withdraw Request -> Admin Approve -> Mark Paid -> Ledger Settlement.
2.  **Decision:**
    *   ✅ **GO:** Canary PASS + Artifacts Secured.
    *   ❌ **NO-GO (Rollback):** Canary FAIL.

### Rollback Decision Matrix
| Trigger | Action |
| :--- | :--- |
| Payout/Withdraw 404/5xx | **Immediate Rollback** |
| Migration Failure | **Immediate Rollback** |
| Ledger Invariant Breach | **Immediate Rollback** |
| Webhook Misclassification | **Immediate Rollback** |
| Latency Spike (No Errors) | Monitor (Hypercare) |
| Queue Backlog (< SLA) | Monitor (Hypercare) |

### 6) Hypercare Tools & Scripts
- **Stuck Job Detector:** `python3 scripts/detect_stuck_finance_jobs.py` (Run every 30m)
- **Daily Recon Report:** `python3 scripts/daily_reconciliation_report.py` (Run daily)
- **Waiver Tracking:** `artifacts/prod_env_waiver_register.md`

### Hypercare Routine (72h)
*   **0-6h:** Every 30m check.
*   **6-24h:** Hourly check.
*   **24-72h:** 3x Daily check.
*   **Focus:** 5xx rates, Queue Backlog, Webhook Failures, Random Ledger Recon.

## 5. Sprint 7 — Execution Checklist (Sign-off)

### 1) Pre-flight (T-60)
- [ ] Release SHA/Tag fixed: __________________
- [ ] Responsibles assigned (Deploy / DB / On-call): __________________
- [ ] `verify_prod_env.py` executed -> Result: PASS / FAIL
    - Log ref: __________________

### 2) Backup (T-30)
- [ ] Prod DB snapshot taken -> Snapshot ID/Path: __________________
- [ ] Snapshot accessibility verified -> PASS / FAIL
- [ ] Rollback restore procedure accessible -> PASS / FAIL

### 3) Deploy + Migration + Smoke (T-15)
- [ ] Deploy completed -> PASS / FAIL
- [ ] `go_live_smoke.sh` executed -> PASS / FAIL
    - [ ] API health 200 -> PASS / FAIL
    - [ ] Admin login -> PASS / FAIL
    - [ ] Payouts router reachable -> PASS / FAIL
    - Log ref: __________________

### 4) Canary Money Loop (T-0) — GO/NO-GO
- [ ] Deposit -> PASS / FAIL (Tx ID: __________________)
- [ ] Withdraw request -> PASS / FAIL (ID: __________________)
- [ ] Admin approve -> PASS / FAIL (Timestamp: __________________)
- [ ] Admin mark paid -> PASS / FAIL (Timestamp: __________________)
- [ ] Ledger settlement / invariant -> PASS / FAIL (Refs: __________________)
- [ ] Canary report completed (`docs/ops/canary_report_template.md`) -> PASS / FAIL

**GO/NO-GO Decision:** GO / NO-GO
**Decider:** __________________ **Date/Time:** __________________

### 5) Hypercare (T+0 -> T+72h)
- [ ] Alerting active (5xx/latency/DB/webhook) -> PASS / FAIL
- [ ] First 6 hours monitoring period applied -> PASS / FAIL
- [ ] 24 hours control report -> PASS / FAIL
- [ ] 72 hours stable -> PASS / FAIL

---
**Canary "GO" Decision Statement (Standard)**
"Prod deploy smoke checks PASS. Canary Money Loop (deposit->withdraw->approve->paid->ledger settlement) PASS. No rollback triggers observed. GO-LIVE confirmed."

## Go-Live Completion Criteria
**Go-Live is considered "COMPLETE" when:**
*   Smoke Tests (Health, Auth, Payouts) **PASS**.
*   Canary Money Loop **PASS** and report filed.
*   No 5xx spikes in the first 2 hours (baseline normal).
*   Withdraw/Payout Queue under control (No SLA breach).
*   No Rollback triggers observed.
*   24-hour control report published (Summary + Metrics + Actions).
