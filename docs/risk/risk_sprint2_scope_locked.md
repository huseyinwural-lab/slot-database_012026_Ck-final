# Risk Sprint 2 Scope: LOCKED

**Sprint:** Faz 6C - Sprint 2
**Focus:** Bet Throttling & Operational Control
**Status:** PLANNED

## 1. In-Scope Features

### A. Bet Throttling (Real-time)
- **Mechanism:** Redis Token Bucket per user.
- **Logic:**
    -   Global Limit: 60 bets / minute.
    -   High Risk Limit: 10 bets / minute (Dynamic throttling).
-   **Enforcement:** API Middleware or Game Engine Hook.

### B. Admin Risk Dashboard
- **UI:** View `RiskProfile` details (Score, History, Flags).
- **Action:** Manual Override (Set Score, Clear Flags).
- **Audit:** Log who changed the risk score and why.

## 2. Out-of-Scope
-   Machine Learning Models.
-   Deposit Blocking (Still only Withdrawal enforcement).
-   Game-specific RTP Anomaly Detection.

## 3. Deliverables
-   `BetThrottleMiddleware` / Hook.
-   `AdminRiskController` (API).
-   Updated `RiskProfile` schema (History table).
