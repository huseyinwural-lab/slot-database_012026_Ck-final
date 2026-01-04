# Incident & Support Runbook (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops  

This runbook defines the incident response flow and escalation boundaries.

---

## 1) Severity levels

- **P0**: full outage, money movement blocked, data integrity risk
- **P1**: major degradation, partial outage
- **P2**: non-critical bug affecting a subset
- **P3**: minor issue

---

## 2) First response checklist (all severities)

1) Confirm scope (one tenant vs many)
2) Capture request IDs and timestamps
3) Check recent deploy SHA
4) Check backend logs and audit trail

---

## 3) Triage quick map

### Auth/login
- verify request URL (frontend)
- check backend `/api/v1/auth/login` errors
- consider rate limits

### Payments/webhooks
- check webhook failure playbook
- verify signature secrets

### Payouts
- check polling errors/timeouts
- check provider connectivity

Legacy references:
- `/docs/ops/webhook-failure-playbook.md`
- `/docs/ops/log_schema.md`

---

## 4) Rollback vs hotfix

Rollback when:
- integrity risk
- payment/payout broken
- migrations failed

Hotfix when:
- isolated change
- verified fix exists

DR reference:
- `/docs/ops/dr_runbook.md`

---

## 5) Escalation

Escalate to:
- **DBA** if migrations/locks/replication issues
- **Security** if credential compromise suspected
- **Payments** if provider failures or reconciliation issues
