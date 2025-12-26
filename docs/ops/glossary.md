# Operational Glossary

## Financial Terms

### Ledger States
*   **Available Balance:** Funds user can bet or withdraw.
*   **Held Balance:** Funds locked for pending withdrawals. Cannot be used for betting.
*   **Ledger Burn:** The final removal of funds from `Held Balance` when a payout is confirmed `Paid` by the provider.
*   **Settlement:** The process of matching a PSP transaction result with our internal Ledger state.

### Transaction States
*   **Created:** Initial record (Deposit).
*   **Pending Provider:** User sent to PSP, waiting for webhook/return.
*   **Requested:** Withdrawal requested by user, funds Held.
*   **Approved:** Withdrawal approved by Admin, ready for Payout.
*   **Payout Submitted:** Payout request sent to PSP (e.g. Adyen), waiting for result.
*   **Paid:** PSP confirmed success. Funds are "Burned" from Ledger.
*   **Payout Failed:** PSP rejected/failed. Funds remain Held until Admin action (Retry/Reject).

## Technical Terms

### Idempotency
The property where an operation (e.g., Webhook, Payout Retry) can be applied multiple times without changing the result beyond the initial application. Critical for preventing double-spending.

### Webhook Signature
A cryptographic hash sent by the PSP (Stripe/Adyen) headers. We calculate the hash of the payload using our Secret. If they match, the request is authentic. **Never bypass this in Prod.**

### Canary
A specific test user/transaction flow executed immediately after deployment to verify the "Money Loop" works before opening traffic to all users.

### Smoke Test
A quick, non-destructive set of checks (Health, Login, Config) to verify the service is running. Does not verify full business logic (that's what Canary is for).
