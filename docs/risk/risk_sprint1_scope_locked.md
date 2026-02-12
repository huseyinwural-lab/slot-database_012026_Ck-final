# Risk Layer Sprint 1 Scope: LOCKED

**Sprint:** Faz 6C - Sprint 1
**Status:** FROZEN
**Date:** 2026-02-16

## 1. Core Objectives (MVP)
The goal of this sprint is to implement a deterministic, rule-based Risk Engine to protect the withdrawal pipeline.

## 2. In-Scope Features
1.  **Real-time Risk Scoring Engine (v1)**
    -   Incremental scoring based on events.
    -   Persistence of user risk profile.
2.  **Velocity Checks**
    -   Tracking specific actions over time windows (e.g., deposits in 24h).
3.  **Withdrawal Guard**
    -   Mandatory risk check step in the withdrawal pipeline.
    -   Auto-Reject vs Manual Review routing.

## 3. Out-of-Scope (Future Sprints)
-   Machine Learning / AI models.
-   Frontend Risk Dashboard (Admin UI changes are minimal/mocked).
-   Deposit Blocking (Only Withdrawal is gated for now).
-   Game-specific anomaly detection (e.g., RTP analysis).

## 4. Deliverables
-   `RiskService` (Backend Service)
-   `RiskProfile` (DB Table)
-   `RiskRule` (Logic)
-   Updated `WithdrawalService` with integration.
