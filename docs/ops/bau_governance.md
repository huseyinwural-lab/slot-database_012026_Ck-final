# BAU Governance Framework

## 1. Principles
- **Safety First:** No manual DB edits without a ticket and approval.
- **Audit Everything:** "Reason" field is mandatory for all changes.
- **On-Call:** 24/7 coverage with 15m response time for P0.

## 2. Meeting Rhythm
- **Daily Standup (09:30):** Review last 24h incidents & deployments.
- **Weekly Ops Review (Mon 14:00):** Review metrics, capacity, and upcoming changes.
- **Monthly Security (1st Thu):** Access review, patch management.

## 3. Change Management
- **Standard Changes:** Pre-approved (e.g. Engine Standard Apply).
- **Normal Changes:** Peer review required (e.g. New Feature Flag).
- **Emergency Changes:** Post-incident review required (Break-glass).

## 4. Incident Management
- **Sev-1 (Critical):** War room, PagerDuty, Hourly comms.
- **Sev-2 (High):** Ticket, Daily comms.
- **Sev-3 (Low):** Next sprint fix.
