# PSP Routing Specification v1

**Status:** ACTIVE
**Strategy:** Success-Rate Priority with Failover.

## 1. Routing Logic
1.  **Primary Check:** Is the user flagged "High Risk"?
    - **Yes:** Route to `Adyen` (Strong 3DS).
    - **No:** Proceed to Priority List.
2.  **Priority List:**
    - 1. Stripe (Lower Fees)
    - 2. Adyen (Higher Acceptance)
    - 3. Manual Wire (Fallback)

## 2. Failover Policy
- **Hard Decline (Do Not Honor):** Stop immediately. Notify user.
- **Soft Decline (Insufficient Funds):** Stop. Notify user.
- **Technical Fail (Timeout/Network):**
  - Retry 1x on same provider (Backoff 2s).
  - If fail, Switch to Next Provider in Priority List.

## 3. Idempotency
- All provider calls MUST include `PaymentIntent.idempotency_key`.
- Double-charge prevention: Ledger only writes on `COMPLETED` intent.
