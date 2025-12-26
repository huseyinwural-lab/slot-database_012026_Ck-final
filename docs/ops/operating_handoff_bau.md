# Operating Handoff & BAU

## Roles & Responsibilities (RACI)

| Activity | Accountable | Responsible | Consulted | Informed |
|----------|-------------|-------------|-----------|----------|
| **Incident Response** | Head of Ops | On-Call Eng | Dev Lead | CTO |
| **Audit Archival** | Compliance Lead | DevOps | Security | Legal |
| **Recon Mismatch** | Finance Lead | Finance Ops | Backend Lead | - |
| **Game Config** | Product Mgr | Game Ops | Compliance | - |

## Operational Rhythm

### Daily
- **09:00 UTC:** Review Audit Archive Jobs (Slack alert if fail).
- **10:00 UTC:** Review Reconciliation Report.

### Weekly
- **Monday:** Ops Review Meeting (Error rates, Latency, Capacity).
- **Friday:** Pre-weekend freeze check.

### Monthly
- **1st:** Retention Purge Verification (Dry run review).
- **15th:** Security/Access Review (Revoke unused Admin keys).

## Contact List
- **Critical Incident:** PagerDuty `critical-ops`
- **Security:** security@casino.com
- **Compliance:** compliance@casino.com
