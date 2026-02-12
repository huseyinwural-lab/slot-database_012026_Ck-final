# Provider Integration Test Plan

**Scope:** Pragmatic Play Mocking

## 1. Mock Server
We need a simple script/service acting as Pragmatic Play.
-   Generates HMAC signatures.
-   Sends `authenticate`, `balance`, `bet`, `result` requests.

## 2. Test Scenarios

### A. Happy Path
1.  **Auth:** Token exchange -> User ID.
2.  **Bet:** $10 Debit -> Balance decreases.
3.  **Win:** $20 Credit -> Balance increases.

### B. Resilience
1.  **Duplicate Bet:** Send same `reference` twice.
    -   *Expect:* 200 OK (Idempotent), Balance changes ONCE.
2.  **Insufficient Funds:** Bet > Balance.
    -   *Expect:* Provider-specific Error Code (e.g., 100 "Not Enough Money").
3.  **Invalid Signature:** Tamper with body.
    -   *Expect:* 403 Forbidden / 400 Bad Request.

### C. Risk Integration
1.  **High Velocity:** Send 100 bets in 1 second.
    -   *Expect:* 429 Error (if mapped) or Provider Error. User flagged.

## 3. Acceptance Criteria
-   `test_pragmatic_flow.py` passes all above scenarios.
