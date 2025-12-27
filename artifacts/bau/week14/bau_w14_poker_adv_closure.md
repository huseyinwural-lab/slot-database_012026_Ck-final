# BAU Sprint 14 Closure Report: Advanced Poker Features

**Sprint Goal:** Enhance Poker offering with Revenue-generating features (MTT Late Reg/Re-entry) and Risk mitigation (Collusion Detection v1).

## Completed Items

### 1. Schema & Migrations (P0)
-   **Model Updates:** Enhanced `PokerTournament` with `reentry_max`, `reentry_price`.
-   **Migration:** Created and applied `T14_poker_risk_mtt` migration to update schema without drift.
-   **Risk Models:** Confirmed `RiskSignal` readiness for Collusion payloads.

### 2. MTT Mechanics (Revenue)
-   **Late Registration:** Implemented time-based registration gating even when `status=RUNNING`.
-   **Re-entry:** Implemented `reentry_tournament` endpoint with:
    -   Eligibility check (Must be BUSTED, within limits).
    -   Ledger integration (Debit Buy-in + Fee).
    -   Prize pool & Entrant count updates.

### 3. Risk Engine (Collusion v1)
-   **Service:** Created `PokerRiskEngine`.
-   **Signals:** Implemented framework for `chip_dumping` and `concentration` signals.
-   **Admin API:** Added endpoints to List Signals and Manually Flag players.

## Validation
-   **MTT Runner:** `/app/scripts/bau_w14_mtt_runner.py`
    -   Verified: Late Reg success, Re-entry success, Re-entry limit enforcement.
-   **Collusion Runner:** `/app/scripts/bau_w14_collusion_runner.py`
    -   Verified: Manual Flag creation and retrieval via Admin API.

## Evidence Package
-   **MTT Log:** `e2e_mtt_late_reg_reentry.txt`
-   **Collusion Log:** `e2e_collusion_signals.txt`

## Next Steps
-   **BAU Sprint 15:** CI Hardening & Release Gates.
