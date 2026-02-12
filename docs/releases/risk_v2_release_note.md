# Risk V2 Release Note

**Version:** `risk-v2-stable`
**Date:** 2026-02-16
**Status:** RELEASED 🟢

## 1. Release Overview
This release introduces the **Risk Layer V2**, adding comprehensive real-time protection against abuse while maintaining financial integrity. It includes real-time scoring, velocity checks, and a manual override system for administration.

## 2. Key Features
- **Real-time Risk Scoring:** Rule-based engine updating scores on Deposits and Withdrawals.
- **Bet Throttling:** Token bucket algorithm protecting against high-frequency betting bots.
- **Withdrawal Guard:** Automatic blocking of withdrawals for High-Risk users (>70 score).
- **Admin Dashboard:** APIs for viewing risk history and applying manual overrides.
- **Audit:** Immutable `risk_history` log for all score changes.

## 3. Migration References
- `20260216_01_risk_profile`: Created risk profile table.
- `20260216_02_risk_history`: Created history table.
- `20260216_03_risk_versioning`: Added versioning and expiry columns.

## 4. Configuration Changes
- **New Env Vars:** None (Uses existing DB/Redis).
- **Feature Flags:** `RISK_ENGINE_ENABLED` (Implicitly active via Service integration).

## 5. Rollback Plan
1.  **Database:** `alembic downgrade 20260215_02_p1_discount_migration` (Warning: destructive to risk data).
2.  **Code:** Revert to tag `risk-v1-baseline` or `p1.2-stable`.
3.  **Operational:** If Redis fails, system fails-open for bets and fails-safe (FLAG) for withdrawals.

## 6. Breaking Changes
- None. Risk layer is additive to the existing transaction pipeline.
