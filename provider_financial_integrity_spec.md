# Provider Financial Integrity Spec

**Goal:** Zero financial drift between Provider and Internal Ledger.

## 1. Transaction State Machine
Extended for granular provider states.

-   **INITIATED:** Adapter received request.
-   **VALIDATED:** Signature/Risk checks passed.
-   **PENDING_LEDGER:** Waiting for DB lock.
-   **SETTLED:** Ledger row committed.
-   **FAILED:** Funds/System error.
-   **ROLLED_BACK:** Provider requested cancellation.

## 2. Idempotency Safeguard
**Critical Rule:** The tuple `(provider_id, provider_tx_id)` MUST be unique.

-   **Implementation:** Postgres/SQLite Unique Index on `game_events` table.
-   **Handling:**
    -   `Insert` -> `IntegrityError` -> `Select Existing` -> `Return Success`.

## 3. Double Settlement Prevention
-   **Win:** Cannot process a "Win" for a Round that doesn't exist? (Optional: Some providers allow "orphan wins", we typically block or create ad-hoc round).
-   **Logic:** `GameRound` tracks `total_win`. If `win_amount` seems duplicate logically (business rule), flag for review. *For Sprint 1: Technical idempotency only.*

## 4. Reconciliation
-   **Daily Job:** Fetch Provider Transaction Report.
-   **Compare:** Sum(Internal) vs Sum(External).
-   **Drift:** Alert if > $0.01.
