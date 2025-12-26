# BAU GOVERNANCE — Operational Order

**Date:** 2025-12-26
**Status:** ACTIVE

## 1. Goal
To make BAU reporting rhythmic, auditable, and action-oriented; to prevent templates from becoming "formality-only"; to ensure actions are tracked and closed.

## 2. Report Production Rules (Non-negotiable)
Every report (W1/W2/M1/30D) must contain the following mandatory fields:

*   **Owner (Single Point of Contact):** The person publishing the report.
*   **Reviewers:** At least one secondary reviewer.
*   **Timestamp:** Date and Time of publication.
*   **Top 3 Findings:** Measurable, concise, and prioritized.
*   **Action List:** Every action must have **Owner + Deadline + Acceptance Criteria**.
*   **Closure Status:** `OPEN` / `IN PROGRESS` / `CLOSED`.

**Rule:** *"A report is INVALID if any action lacks an Owner or Deadline."*

## 3. Action Tracking Standard
*   **Single Source:** All actions are tracked in a single backlog (Jira, Linear, or GitHub Issues).
*   **Linkage:** Actions opened in reports must be linked to their corresponding Ticket IDs.
*   **Weekly Ops Review Routine:**
    1.  Review and close/reschedule actions from the previous week.
    2.  List and address "Overdue" actions.
    3.  Review new findings.

## 4. Archiving & Naming Convention
Reports must follow this standardization for auditability:

*   **W1 Ops Review:** `bau_weekly_ops_review_YYYY-MM-DD.md`
*   **W2 Security Review:** `bau_security_review_YYYY-MM-DD.md`
*   **M1 KPI Review:** `bau_kpi_review_YYYY-MM-DD.md`
*   **30D Closeout:** `bau_30d_closeout_YYYY-MM-DD.md`

**Location:** Store in `/app/artifacts/bau/` (create directory if needed).

## 5. Escalation Rules
Escalation is **mandatory** under the following conditions:

*   **SLO Breach:** Availability, Latency, or Webhook Rate below target.
*   **Recon High Risk:** Any `HIGH` risk mismatch found in `daily_reconciliation_report.py`.
*   **Waiver Breach:** Deadline passed for a waiver in `prod_env_waiver_register.md`.
*   **Finance Stuck:** Stuck transactions exceeding SLA (e.g., > 2 hours).

**Escalation Output:**
*   Incident Record + Short RCA + Remediation Plan.

## 6. BAU Success Criteria (First 30 Days)
*   [ ] All 4 scheduled reports (W1, W2, M1, 30D) published on time.
*   [ ] ≥ 70% of opened actions are closed within their deadline.
*   [ ] All `HIGH` risk waivers are closed or formally re-planned.
*   [ ] SLOs are actively measured, and a trend report is available.

## 7. Initiation Instruction
Upon approval of this order:
1.  Generate the **W1 Ops Review** report.
2.  Define at least **3 Actions** in the W1 report.
3.  Add these actions to the tracking backlog immediately.
4.  The next review meeting must start with "Action Closures".
