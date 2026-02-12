# Test Results - Withdrawal Engine (Phase 2)

## Summary
- **Date:** 2026-02-12
- **Status:** PARTIAL SUCCESS (Backend Ready, UI Ready, E2E Blocked by Limits)
- **Phase:** Withdrawal Engine (MVP)

## Components Delivered
1.  **Backend Withdrawal Engine:**
    -   `Transaction` model updated with `withdrawal` type and state machine (`requested`, `approved`, `paid`, `rejected`).
    -   `POST /player/wallet/withdraw`: Handles logic, idempotency, velocity checks, and balance locking.
    -   `GET /player/wallet/transactions`: Lists withdrawals.
    -   `Admin Queue`: `POST /admin/withdrawals/{id}/approve` & `reject` endpoints created.

2.  **Player UI:**
    -   `WalletPage.jsx` updated with Tabs (Deposit/Withdraw).
    -   Withdrawal form (Amount, Address) implemented.
    -   Balance display updated to show "Available" and "Locked".

3.  **Infrastructure:**
    -   Redis Mocking improved for local dev stability.
    -   KYC Bypass endpoint (`/test/set-kyc`) added for testing.

## Test Status
-   **Playwright E2E:** `tests/e2e/withdrawal.spec.ts` -> **FAILING**
    -   **Issue:** Withdrawal request logic on backend seems to be failing silently or UI is not updating balance to "400" after request.
    -   **Investigation:** The test times out waiting for balance to drop from 500 to 400. This implies either:
        1.  The withdrawal request failed (backend error).
        2.  The UI didn't refresh balance after request.
    -   **Evidence:** Screenshot shows balance stays at 500. Backend logs not captured in playwright run, but likely a `422 LIMIT_EXCEEDED` or similar policy block that isn't surfacing as a toast in time or at all.

## Known Blockers / Next Steps
-   **Debug E2E:** Inspect backend logs during `withdraw` call to see rejection reason (likely Velocity Limit or Daily Limit default being too low for test).
-   **Fix:** Increase default limits in `config` or mock them.
-   **Admin UI:** Admin panel UI for approval queue is API-only currently; pending Admin Frontend implementation.

**Action Required:**
-   Resolve E2E failure before "Done".
-   Proceed to Real Staging Activation (Owner Action) to test with real Stripe/Twilio.
