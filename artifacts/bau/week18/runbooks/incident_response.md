# Incident Response Runbook

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
