# Final Post-Go-Live Program Order (90 Days)

**Goal:** Maintain production stability, increase verifiability of financial flows, strengthen security and compliance, reduce operational costs, and scale revenue-generating product functions.

---

## A) RELIABILITY TRACK (SRE / Ops)

### 0–14 Days (P0)
1.  **Define SLO/SLI & Dashboard Integration**
    *   Metrics: API availability, p95 latency, webhook success rate, payout SLA.
    *   Goal: Automated weekly report generation.
2.  **Incident Management Standard**
    *   Define severity levels, escalation routes, postmortem templates.
    *   Create a "1-pager" incident playbook.
3.  **Cron/Scheduler Standardization**
    *   For `detect_stuck_finance_jobs.py` and `daily_reconciliation_report.py`:
        *   Scheduling (cron/systemd/k8s cronjob).
        *   Log retention policies.
        *   Failure alerting.

### 15–90 Days (P1)
*   **Automated Capacity Reporting:** DB pool usage, CPU, queue backlog trends.
*   **Chaos-Lite Testing:** Periodic testing of webhook duplicate/fail scenarios in a prod-like environment.

---

## B) SECURITY & COMPLIANCE TRACK

### 0–14 Days (P0)
1.  **Waiver Register Closure Plan**
    *   For missing/test secrets:
        *   Route: Procurement/Rotation.
        *   Owner + Deadline.
    *   "Waiver Open" SLA: Max 30 days.
2.  **Secrets Management**
    *   Centralized management (Vault/SSM/K8s secrets).
    *   Rotation procedures + Audit logs.
3.  **Access Control Review**
    *   Prod admin access: Least privilege, MFA, logged access.

### 15–90 Days (P1)
*   **OWASP ASVS Lite Checklist:** + Plan for 2 penetration tests per year.
*   **PCI Approach:** Gap analysis (if card/PSP scope expands).

---

## C) FINANCE / RECONCILIATION MATURITY TRACK

### 0–14 Days (P0)
1.  **Actionable Reconciliation Outputs**
    *   Enhance `daily_reconciliation_report.py`:
        *   Risk classification (LOW/MED/HIGH).
        *   Action recommendations (retry, manual review, escalate).
    *   Result: Ops team can close tasks based on the report.
2.  **Manual Override Procedure**
    *   For stuck payout/withdraw situations:
        *   Who approves?
        *   What records are kept?
        *   What logs are appended?

### 15–90 Days (P1)
*   **Weekly "Ledger vs Wallet" Reconciliation:** Full scan.
*   **Settlement Reporting:** PSP vs Internal difference analysis.

---

## D) PRODUCT & GROWTH TRACK

### 0–14 Days (P0)
1.  **Real User Flow Metrics**
    *   Onboarding funnel.
    *   Deposit conversion.
    *   Withdrawal completion time.
2.  **Ops UI Improvements**
    *   Payout/Withdraw queue screens:
        *   Quick filters.
        *   Stuck badges.
        *   "Retry-safe" action buttons (idempotent only).

### 15–90 Days (P1)
*   **A/B Test Infrastructure:** Simple feature flags.
*   **Campaign/Bonus Engine Improvements:** Revenue-focused.

---

## Management Model (Weekly Rhythm)
*   **Weekly (30 min):** Ops health review (SLO + incidents + recon risks).
*   **Bi-Weekly:** Security review (waiver + access).
*   **Monthly:** Product KPI review (conversion + retention).

---

## Immediate Action Set (First 2 Weeks)
1.  [ ] Define SLO/SLIs and add to dashboard.
2.  [ ] Connect scripts to cron + add failure alerts.
3.  [ ] Open rotation/completion tickets for secrets in Waiver Register.
4.  [ ] Update Reconciliation Report with risk classes and action recommendations.
5.  [ ] Write Manual Override Procedure and add to runbook.
6.  [ ] Plan backlog items for Ops queue "stuck badge" + filters.
