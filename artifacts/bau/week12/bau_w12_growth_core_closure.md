# BAU Sprint 12 Closure Report: Growth Core

**Sprint Goal:** Implement the foundational Growth Core, featuring an Affiliate System and Automated CRM triggers based on player behavior.

## Completed Items
1.  **Affiliate System:**
    -   Implemented `Affiliate`, `AffiliateLink`, `AffiliateAttribution` models.
    -   Implemented `AffiliateEngine` service for attribution and commission calculation (CPA).
    -   Implemented `affiliates` API endpoints (Create Affiliate, Create Link, List Links).
    -   Integrated attribution hook into `PlayerAuth` (Register).

2.  **CRM Automations:**
    -   Implemented `GrowthEvent` stream and `CRMEngine`.
    -   Implemented `FIRST_DEPOSIT` trigger to award `Welcome Bonus`.
    -   Integrated triggers into `Payments` webhook (`deposit_captured`).

3.  **Validation:**
    -   Created E2E Test Runner: `/app/scripts/bau_w12_runner.py`.
    -   Verified full loop: Affiliate Link -> Signup -> Deposit -> Commission -> CRM Bonus Grant.

## Evidence Package
-   **Execution Log:** `e2e_affiliate_crm_growth_loop.txt` (Successful E2E run).
-   **Metrics Snapshot:** `growth_metrics_snapshot.json` (Affiliate & Link stats).

## Technical Debt & Known Issues
-   **Schema Drift:** Several manual schema patches were applied (`fix_admin_schema.py`, `fix_affiliate_schema.py`) due to unstable Alembic workflow.
-   **Duplicate Models:** Resolved duplicate model definitions (`Affiliate`, `LedgerTransaction`) in `sql_models.py` vs modular files.
-   **Service Structure:** Resolved ambiguous `slot_math` package structure.

## Next Steps
-   **BAU Sprint 13:** VIP Tiers & Loyalty System.
-   **Tech Debt:** Prioritize fixing Alembic migration workflow to avoid further manual patching.
