# Risk Scoring Model v1

**Type:** Deterministic / Rule-Based
**Base Score:** 0 (Low Risk)

## 1. Scoring Logic
Score is cumulative but capped at 100.
`Current Score = Previous Score + Σ(Rule Impact)`

### A. Velocity Rules
| Rule Name | Condition | Impact | Decay |
|-----------|-----------|--------|-------|
| **Rapid Deposit** | > 3 deposits in 10 mins | +30 | 24h |
| **Rapid Withdraw** | > 2 requests in 1 hour | +20 | 24h |
| **High Velocity Bet** | > 100 bets in 5 mins | +10 | 1h |

### B. Pattern Rules
| Rule Name | Condition | Impact | Decay |
|-----------|-----------|--------|-------|
| **Churn (Dep->Wdraw)** | Withdraw within 1h of Deposit | +40 | 7 days |
| **Big Win** | Single Win > 100x Bet | +20 | 24h |
| **New Device** | Login from new device | +15 | 7 days |
| **IP Mismatch** | Geo distance > 500km in 1h | +50 | 30 days |

## 2. Thresholds & Actions

| Score Range | Risk Level | Action (Withdrawal) | Action (General) |
|-------------|------------|---------------------|------------------|
| **0 - 39** | **LOW** | **ALLOW** (Auto-Process) | Monitor |
| **40 - 69** | **MEDIUM** | **SOFT FLAG** (Manual Review) | Alert Admin |
| **70 - 100** | **HIGH** | **HARD BLOCK** (Auto-Reject) | Suspend Account |

## 3. Decay Strategy (Future P2)
- Scores naturally decay over time to allow rehabilitation.
- For Sprint 1: Manual reset or fixed decay job.
