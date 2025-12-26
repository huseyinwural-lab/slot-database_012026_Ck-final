# Risk v1 Active Rules (BAU W8)

**Status:** ACTIVE
**Enforcement:** Automated

## 1. Velocity Rules
*Detects rapid-fire financial actions indicative of account takeover or botting.*

| Rule ID | Condition | Time Window | Action | Severity |
|---------|-----------|-------------|--------|----------|
| `VEL-001` | Deposits > 5 | 1 Minute | Flag Player | Medium |
| `VEL-002` | Withdrawals > 3 | 10 Minutes | Hold Withdrawals | High |
| `VEL-003` | Failed Logins > 10 | 5 Minutes | Block Login | Critical |

## 2. Payout Anomaly
*Detects potential chip dumping or RNG manipulation.*

| Rule ID | Condition | Action | Severity |
|---------|-----------|--------|----------|
| `PAY-001` | ROI > 5000% (Single Session) | Flag Player | High |
| `PAY-002` | Net Win > $10,000 (New Account) | Hold Withdrawals | Critical |

## 3. Multi-Account (Ops)
*Correlates identities.*

- **Signal:** Same IP + Device Fingerprint on > 2 Accounts.
- **Action:** Link accounts in Risk Dashboard, prevent concurrent play.

## Enforcement Actions
1.  **Flag:** Visible in Admin UI, no blocking.
2.  **Hold Withdrawals:** Auto-reject withdrawals until manual review.
3.  **Block Gameplay:** Prevent `GAME_LAUNCH` and `BET`.
