# Risk Layer Scope (Faz 6C)

**Version:** 0.1 (Pre-Design)

## 1. Objective
Protect the platform from bonus abuse, money laundering, and technical anomalies without hurting genuine player experience.

## 2. Core Components

### A. Risk Scoring Matrix (Real-time)
Every `Player` has a dynamic `risk_score` (0-100).
- **High Risk Triggers:**
    - High velocity deposits (>3 in 10 mins).
    - Withdrawal immediately after deposit (churn).
    - 100% win rate on high variance games (anomaly).
    - Multiple accounts (IP/Device match).

### B. Withdrawal Anomaly Detection (Async)
Before auto-approving withdrawals:
1. **Rule:** `Win > 10x Total Deposit` -> Manual Review.
2. **Rule:** `Bonus Wagering < Requirement` -> Auto Reject.
3. **Rule:** `Cross-Tenant Pattern` -> Flag.

### C. Action Policies
| Risk Level | Deposit Limit | Withdrawal | Bonus Access |
|------------|---------------|------------|--------------|
| **Low** | Standard | Instant | Full |
| **Medium** | Standard | Manual 24h | Restricted |
| **High** | Blocked | Blocked | None |

## 3. Data Requirements
- `TelemetryEvent` table (Login IP, Device ID).
- `GameRound` history (Win rates).
- `Transaction` velocity.

## 4. Implementation Phasing
- **Phase 1:** Simple Rules Engine (Hardcoded limits).
- **Phase 2:** Scoring System (Points based).
- **Phase 3:** ML/AI Anomaly Detection (Future).
