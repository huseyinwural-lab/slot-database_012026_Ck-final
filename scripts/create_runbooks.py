import os

RUNBOOK_DIR = "/app/artifacts/bau/week18/runbooks"
os.makedirs(RUNBOOK_DIR, exist_ok=True)

incident_response = """# Incident Response Runbook

## Severity Levels
- **SEV-1 (Critical):** Service Down, Data Loss, Security Breach. ETA: 15m response.
- **SEV-2 (High):** Feature broken, Performance degradation. ETA: 1h response.
- **SEV-3 (Medium):** Minor bug, cosmetic. ETA: Business hours.

## Response Steps

### 1. Acknowledge & Assess
- Check `AlertEngine` logs or dashboard.
- Identify affected component (Backend, DB, Gateway).
- Open Incident Ticket (Jira/PagerDuty).

### 2. Mitigation (Stop the bleeding)
- If DB Load High: Check `active_queries`. Kill blockers.
- If Bad Deploy: Run `rollback_procedure.md`.
- If External API Down: Enable `KillSwitch` for that provider.

### 3. Investigation (RCA)
- Check Logs: `grep "ERROR" /var/log/supervisor/backend.err.log`.
- Check Audit Trail: Who changed what recently?
- Check Metrics: Payment success rates.

### 4. Resolution
- Apply fix (Hotfix deploy or Config change).
- Verify health: `curl /api/health`.

### 5. Post-Mortem
- Write RCA document.
- Create preventative backlog items.
"""

rollback_procedure = """# Rollback Procedure

## When to Rollback?
- Deployment failed health checks.
- Critical bug found immediately after deploy.
- Migration failure affecting data integrity.

## Steps

### 1. Database Rollback (If Migration involved)
- Check current head: `alembic current`
- Downgrade to previous revision: `alembic downgrade -1`
- **Warning:** Data loss possible if columns dropped. Verify data backup first.

### 2. Application Rollback
- Revert Git branch to previous tag: `git checkout <previous_tag>`
- Or use Container Image: `docker pull image:previous_tag`

### 3. Restart Services
- `supervisorctl restart backend`
- `supervisorctl restart frontend`

### 4. Verify
- Check `/api/health`
- Run Smoke Tests: `python3 /app/scripts/release_smoke.py`
"""

reconciliation_playbook = """# Reconciliation Exception Playbook

## Purpose
Investigate and resolve `ReconciliationFinding` (Mismatch between PSP and Ledger).

## Scenarios

### Case 1: Missing in Ledger (Money at PSP, not in User Wallet)
- **Cause:** Webhook failure, Timeout.
- **Action:**
  1. Verify PSP transaction status (Dashboard).
  2. Manually credit user via Admin API or re-run webhook.
  3. Mark finding as `RESOLVED`.

### Case 2: Missing in PSP (Money in User Wallet, not at PSP)
- **Cause:** Phantom transaction, Fraud.
- **Action:**
  1. Verify NO money received at PSP.
  2. **CRITICAL:** Debit user wallet immediately (Correction).
  3. Investigate `payment_intent` logs.

### Case 3: Amount Mismatch
- **Cause:** Currency conversion, Fee deduction mismatch.
- **Action:**
  1. Calculate difference.
  2. Post adjustment to Ledger (`type=adjustment`).
  3. Update Finance Config if systematic error.
"""

with open(f"{RUNBOOK_DIR}/incident_response.md", "w") as f:
    f.write(incident_response)

with open(f"{RUNBOOK_DIR}/rollback_procedure.md", "w") as f:
    f.write(rollback_procedure)

with open(f"{RUNBOOK_DIR}/reconciliation_playbook.md", "w") as f:
    f.write(reconciliation_playbook)

print("Runbooks created.")
