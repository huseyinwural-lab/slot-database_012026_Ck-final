# Faz 6A Sprint 2 Scope Freeze

**Phase:** Faz 6A - Sprint 2
**Focus:** E2E Integration & Financial Hardening
**Status:** EXECUTION ACTIVE 🚀
**Date:** 2026-02-16

## 1. Scope
This sprint focuses on validating the Pragmatic Play integration through rigorous End-to-End HTTP testing, enforcing idempotency at the database level, and implementing reconciliation jobs.

### A. End-to-End HTTP Testing
-   **Mock Server:** Simulate Pragmatic Play HTTP requests.
-   **Flows:** Auth -> Balance -> Bet -> Win -> Rollback.
-   **Validation:** Verify wallet balance consistency and correct HTTP status codes/payloads.

### B. Idempotency Enforcement
-   **Database:** Verify `(provider, provider_event_id)` unique constraint on `game_events`.
-   **Logic:** Ensure duplicate callbacks return cached success responses without side effects.

### C. Reconciliation Job
-   **Logic:** Scheduled job to compare internal ledger vs. (mocked) provider reports.
-   **Metrics:** Alert on financial drift.

### D. Failure Mode Hardening
-   **Scenario:** Database Lock Timeouts, Redis Failures, Signature Mismatches.
-   **Output:** Deterministic error mapping.

## 2. Exclusions
-   **Front-end Integration:** Game launcher UI is out of scope.
-   **Multi-Provider Routing:** Focusing solely on Pragmatic.

## 3. Success Criteria
-   `test_pragmatic_e2e_http.py` PASS.
-   `test_provider_idempotency.py` PASS.
-   Wallet Drift = 0.00.
