# Risk Layer Execution Plan (Faz 6C)

**Status:** PLANNED
**Start Date:** Immediate
**Prerequisites:** P1.2 (Discount) Complete

## 1. Context & Motivation
With the introduction of the Discount Engine (P1.2) and the upcoming provider integrations, the platform's abuse surface has expanded. A dedicated Risk Layer is now critical to prevent bonus abuse, money laundering, and arbitrage.

## 2. Core Components (Scope)

### A. Risk Scoring Engine (Real-time)
- **Goal:** Assign a dynamic `risk_score` (0-100) to every player session.
- **Inputs:**
    - Transaction Velocity (Deposits/Withdrawals per hour)
    - IP/Device Fingerprint changes
    - Win-rate anomalies (e.g., > 3 SD from RTP)
- **Output:** `Player.risk_score` update + `RiskEvent` log.

### B. Event Matrix
| Event | Risk Weight | Action Threshold |
|-------|-------------|------------------|
| Rapid Deposit (3x < 10min) | +10 | > 50 (Watchlist) |
| Withdrawal w/o Gameplay | +30 | > 70 (Manual Review) |
| Bonus Wagering Arbitrage | +50 | > 90 (Auto Block) |
| Multi-Account Match | +100 | Immediate Ban |

### C. Withdrawal Guardrails
- **Logic:** Intercept `WithdrawalService` request.
- **Check:** `IF risk_score > Threshold OR profit > 10x deposit THEN require_approval`.

## 3. Implementation Plan (Sprints)

### Sprint 1: Foundation (Faz 6C.1)
- [ ] Define `RiskRule` and `RiskScore` models.
- [ ] Implement `RiskService` skeleton.
- [ ] Instrument `Transaction` flow to emit events to Risk Engine.

### Sprint 2: Scoring Logic (Faz 6C.2)
- [ ] Implement Velocity Checks (Redis-based sliding window).
- [ ] Implement Basic Anomaly Rules.

### Sprint 3: Enforcement (Faz 6C.3)
- [ ] Integrate with Withdrawal Workflow.
- [ ] Build Risk Dashboard (Admin UI).

## 4. Dependencies
- **Data:** Needs `LedgerTransaction` history (Available).
- **Redis:** Required for velocity tracking (Available).
