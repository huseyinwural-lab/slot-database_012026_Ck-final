# Sprint 1 Exit Criteria

**Sprint:** Faz 6C - Sprint 1
**Gate:** Production Release

## 1. Functional Success
- [ ] **Data Structure:** `RiskProfile` table created and linked to Users.
- [ ] **Scoring:** Events (Deposit, Login) correctly update `risk_score`.
- [ ] **Enforcement:**
    -   Withdrawal < Threshold -> Auto PASS.
    -   Withdrawal > Hard Threshold -> Auto BLOCK.
    -   Withdrawal in Mid Range -> FLAG (Stubbed as 'PENDING').
- [ ] **Velocity:** 3x Rapid deposits trigger score increase.

## 2. Technical Success
- [ ] **Performance:** Risk check latency < 50ms.
- [ ] **Resilience:** Redis failure defaults to "Allow" (Fail-Open) or "Block" (Fail-Closed) - *Decision: Fail-Closed for Withdrawals*.
- [ ] **Tests:** Unit tests covering all 5 core rules.

## 3. Documentation
- [ ] Architecture Diagram updated.
- [ ] API Docs for Risk Management endpoints.
