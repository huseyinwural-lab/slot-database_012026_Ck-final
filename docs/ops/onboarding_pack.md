# Ops / Engineer Onboarding Pack

**Welcome to the Platform Operations Team.**
Goal: Enable you to run the system safely within 2 hours.

---

## 1. System Architecture (1-Pager)
*   **Backend:** FastAPI (Python), Async SQLAlchemy.
*   **Frontend:** React (Admin + Player).
*   **Database:** PostgreSQL (Core Data + Ledger).
*   **Queue:** Redis/Arq (Background jobs).
*   **Integrations:** Stripe (Deposit), Adyen (Deposit/Payout).

## 2. The Money Flow (Critical)
Understanding this is mandatory for handling finance incidents.

1.  **Deposit:** User -> Stripe/Adyen -> Webhook -> **Ledger Credit** (+Available).
2.  **Withdraw Request:** User Request -> **Ledger Hold** (-Available, +Held) -> Transaction Created (State: `requested`).
3.  **Approval:** Admin Review -> Transaction State: `approved`.
4.  **Payout Execution:** Admin/System -> PSP (Adyen) -> Transaction State: `payout_submitted`.
5.  **Settlement:**
    *   **Success:** Webhook (Paid) -> Transaction State: `paid` -> **Ledger Burn** (-Held).
    *   **Failure:** Webhook (Failed) -> Transaction State: `payout_failed` -> **Funds remain Held** (Manual Review required to Refund or Retry).

## 3. Day-1 Tasks (Get your hands dirty)
1.  **Verify Environment:** Run `python3 scripts/verify_prod_env.py`. Check output.
2.  **Smoke Test:** Run `bash scripts/go_live_smoke.sh`. confirm API health.
3.  **Check Backlog:** Run `python3 scripts/detect_stuck_finance_jobs.py`. If output is not empty, report it.
4.  **Read the Runbook:** Skim `/app/docs/ops/go_live_runbook.md`, focus on the "Rollback Matrix".

## 4. Day-2 Tasks (BAU Contribution)
1.  **Generate a Report:** Run `daily_reconciliation_report.py` and format it using the W1 template.
2.  **Open an Action:** Identify one improvement or risk from the report and open a ticket.

## 5. Critical "DO NOTs" (The Red Lines)
*   ❌ **NEVER** run `db_restore_drill.sh` (Restore Phase) on Production DB. Backup phase is fine.
*   ❌ **NEVER** manually update Transaction State in DB (`UPDATE transaction SET ...`) without a second-person review and Audit Log entry.
*   ❌ **NEVER** ignore a **Canary FAIL**. It means NO-GO.
*   ❌ **NEVER** leave a "High Risk" waiver open past its deadline without Escalation.
