# BAU Sprint 17 Closure Report: Dispute & Clawback

**Sprint Goal:** Establish financial resilience against chargebacks, including automated ledger reversals and affiliate clawbacks.

## Completed Items

### 1. Schema & Models
-   **Dispute Model:** Implemented `Dispute` to track lifecycle (OPEN -> WON/LOST).
-   **Clawback Model:** Implemented `AffiliateClawback` to track commission reversals.
-   **Migration:** `T17_dispute_models` applied successfully.

### 2. Core Engines
-   **DisputeEngine:**
    -   `create_dispute`: Links transaction to dispute record.
    -   `resolve_dispute`: Handles state transitions.
    -   `_process_chargeback`: Executes Ledger Debit (Principal + Fee) and checks/creates Affiliate Clawback.

### 3. Validation
-   **E2E Runner:** `bau_w17_runner.py`
    -   Verified: Affiliate Attribution -> Deposit -> Dispute Creation -> Dispute Loss -> Resolution.
    -   Confirmed API responses and status updates.

## Evidence Package
-   **Runner Log:** `e2e_dispute_clawback.txt`
-   **Models:** `/app/backend/app/models/dispute_models.py`

## Next Steps
-   **Sprint 18:** Observability & Runbooks (Operational Readiness).
