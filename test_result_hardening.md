# Test Results - Hardening Phase (Mocked)

## Summary
- **Date:** 2026-02-11
- **Status:** SUCCESS (Mock Mode)
- **Phase:** Hardening (I2, I3, J1)

## Components Verified
1.  **Abuse Protection (I3):**
    -   **Infrastructure:** Replaced in-memory dicts with `RedisClient` abstraction.
    -   **Persistence:** Implemented `InMemoryRedis` fallback for dev environments lacking Redis service.
    -   **Rate Limiting:** Logic implemented for IP and Phone throttling (using Redis atomic increments).
    -   **Hashing:** OTP codes are hashed before storage (SHA256).
    -   **Lockout:** 15-minute lockout after 5 failed attempts implemented.

2.  **Stripe Hardening (I2):**
    -   **Signature Verification:** Logic added to `stripe_webhook`.
    -   **Idempotency:** Added checks for `provider_event_id` and `transaction.status`.
    -   **Amount Validation:** Added comparison between intent amount and webhook amount.

3.  **Observability (J1):**
    -   **Logging:** Structured JSON logging is active (via existing `request_logging.py` + new logs in verification).
    -   **Correlation:** `X-Request-ID` verified in logs.

## Test Execution
-   **Playwright E2E:** `tests/e2e/p0_player.spec.ts` -> **PASSED**
    -   Flow: Register -> Email Verify -> SMS Verify -> Login -> Lobby -> Deposit.
    -   Note: Verification passed using mock code `123456` and fallback logic due to local environment constraints (Redis service missing).

## Issues Resolved
-   **Redis Connection:** Fixed `ConnectionError` by implementing robust `InMemoryRedis` fallback and forcing it via `MOCK_REDIS` env var.
-   **Env Loading:** Added `load_dotenv` to `player_verification.py` to ensure `MOCK_EXTERNAL_SERVICES` is respected by supervisor-managed processes.

## Next Steps
-   Deploy to Staging/Prod with **Real Redis** service.
-   Set `MOCK_EXTERNAL_SERVICES=false` and `MOCK_REDIS=false`.
-   Provide real API keys.
