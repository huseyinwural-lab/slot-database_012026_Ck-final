# Operating Handoff (BAU) Order — Post-Project

**Date:** 2025-12-26
**Status:** BAU ACTIVE

## 1. Goal
Ensure seamless operation of the platform after project closure; clarify ownership and decision-making mechanisms; guarantee controlled closure of risks (including waivers).

## 2. BAU Ownership (RACI)
*   **Ops / SRE Owner:** Uptime, Incident Management, Alerting, Capacity Planning.
*   **Security Owner:** Secrets Management, Access Control, Waiver Closures, Key Rotation.
*   **Finance / Recon Owner:** Stuck Job Detection, Reconciliation Reports, Manual Override Procedures.
*   **Product Owner:** KPIs, Roadmap Execution, Operations UI Requests.

## 3. Single Source Documents
*   **Runbook:** `/app/docs/ops/go_live_runbook.md`
*   **Closeout Pack:** `/app/docs/roadmap/executive_closeout_pack.md`
*   **90-Day Roadmap:** `/app/docs/roadmap/post_go_live_90_days.md`
*   **Recon/Hypercare Artifacts:** `/app/artifacts/*`

## 4. Operational Rhythm
*   **Weekly (30 min):** Ops Health Review (SLO/SLI, Incidents, Recon Risks).
*   **Bi-Weekly:** Security Review (Waiver Status, Access Reviews, Rotation).
*   **Monthly:** Product KPI Review (Conversion, Retention, Payout SLA).

## 5. Checkpoints
*   **T+7 Days:** No "High Risk" items remaining in Waiver Register, or a concrete plan approved.
*   **T+14 Days:** Recon Report and Stuck Detector must be fully automated (including failure alerts).
*   **T+30 Days:** SLO targets are being measured and reported; first capacity trend report generated.

## 6. Immutable Rules (Prod Discipline)
*   **Canary FAIL = NO-GO:** Applies to all future deployments/cutovers.
*   **Manual Override:** Always audited and requires two-person approval (for finance operations).
*   **Secrets/Test Keys:** Managed via deadlines, not indefinite waivers.

## 7. Handover Statement
"The platform has been successfully handed over to the BAU operating model. Ownerships are assigned, the operational rhythm is established, and control points are defined. Open risks will be tracked and closed via the roadmap and waiver register."
