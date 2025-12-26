# Post-Go-Live Prioritized Backlog (Sprint 8+)

**Status:** ACTIVE
**Source:** Handover Protocol

## P0 — Immediate Operational Risks (Week 1-2)
**Goal:** Close security gaps and ensure automation stability.

- [ ] **Waiver/Secrets Closure**
    - **Ref:** `/app/artifacts/prod_env_waiver_register.md`
    - **Task:** Complete missing/test secrets, execute rotation plan.
    - **Definition of Done:** Waiver count = 0 (or only low-risk items with approved deadlines).

- [ ] **Scheduled Jobs Productionizing**
    - **Scripts:** `detect_stuck_finance_jobs.py`, `daily_reconciliation_report.py`
    - **Task:** Deploy to Cron/K8s CronJob, configure log retention, setup failure alerts (PagerDuty/Slack).
    - **Definition of Done:** Runs daily automatically + Failure triggers alert.

- [ ] **Manual Override Procedure (Two-Person Rule)**
    - **Task:** Document the exact SQL/Admin steps for fixing stuck finance states.
    - **Constraint:** Must require 2 people (Doer + Approver) and Audit Log entry.
    - **Definition of Done:** Procedure added to Runbook.

- [ ] **Incident Playbook & Escalation Test**
    - **Task:** Define Severity levels (Sev1/Sev2), Escalation matrix, Rollback authority.
    - **Definition of Done:** One Tabletop exercise completed and recorded.

---

## P1 — Value & Efficiency (Week 2-4)
**Goal:** Reduce toil and increase visibility.

- [ ] **SLO/SLI Dashboard**
    - **Metrics:** Availability, p95 Latency, Webhook Success Rate, Payout SLA (<24h).
    - **Definition of Done:** Automated weekly report generation.

- [ ] **Deep Reconciliation**
    - **Task:** Weekly full scan of "Ledger vs Wallet" consistency.
    - **Definition of Done:** Automated ticket creation for any mismatch found.

- [ ] **Ops UI Improvements**
    - **Task:** Add "Stuck Badge", Quick Filters, and "Safe Retry" button (idempotent) to Admin Panel.
    - **Definition of Done:** Reduced manual DB intervention count.

---

## P2 — Scale & Growth (Month 2+)
**Goal:** Optimize product and security posture.

- [ ] **KPI Instrumentation**
    - **Metrics:** Onboarding Funnel, Repeat Deposit Rate, Withdraw Completion Time.
    - **Definition of Done:** M1 KPI Review populated with real data.

- [ ] **Feature Flags & Controlled Release**
    - **Task:** Implement Feature Flag system for gradual rollouts (Canary deployments).
    - **Definition of Done:** Riskier modules can be toggled without deploy.

- [ ] **Security Hardening**
    - **Task:** Least Privilege review, Enforce MFA for Admin, Dependency Scanning.
    - **Definition of Done:** Security Review actions closed regularly.

---

## Executive Summary
*   **P0:** Close Secrets/Waivers, Automate Jobs, Finalize Manual Override & Incident Playbook.
*   **P1:** SLO Dashboard + Deep Recon + Ops UI Efficiency.
*   **P2:** KPIs, Feature Flags, Security Hardening.
