# Velocity Rules Specification

**Implementation:** Redis Sliding Windows or Token Buckets

## 1. Defined Windows

| Context | Metric | Window | Limit | Action |
|---------|--------|--------|-------|--------|
| **Betting** | Count | 5 min | 1000 | Throttle API |
| **Withdrawal** | Count | 1 hour | 2 | Soft Flag |
| **Withdrawal** | Amount | 24 hours | $5,000 | Soft Flag |
| **Deposit** | Count | 10 min | 5 | Increase Risk Score |
| **Deposit** | Amount | 24 hours | $10,000 | Monitor |

## 2. Redis Key Structure
-   `risk:velocity:{metric}:{user_id}:{window_epoch}`
-   Example: `risk:velocity:withdraw_count:u-123:170000` (bucketed)

## 3. Enforcement
-   Velocity checks run **before** scoring logic.
-   Limit breach -> Triggers immediate Rule Hit (+Score) or direct Block.
