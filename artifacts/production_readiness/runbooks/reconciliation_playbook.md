# Reconciliation Exception Playbook

## Purpose
Investigate and resolve `ReconciliationFinding` (Mismatch between PSP and Ledger).

## Scenarios

### Case 1: Missing in Ledger (Money at PSP, not in User Wallet)
- **Cause:** Webhook failure, Timeout.
- **Action:**
  1. Verify PSP transaction status (Dashboard).
  2. Manually credit user via Admin API or re-run webhook.
  3. Mark finding as `RESOLVED`.

### Case 2: Missing in PSP (Money in User Wallet, not at PSP)
- **Cause:** Phantom transaction, Fraud.
- **Action:**
  1. Verify NO money received at PSP.
  2. **CRITICAL:** Debit user wallet immediately (Correction).
  3. Investigate `payment_intent` logs.

### Case 3: Amount Mismatch
- **Cause:** Currency conversion, Fee deduction mismatch.
- **Action:**
  1. Calculate difference.
  2. Post adjustment to Ledger (`type=adjustment`).
  3. Update Finance Config if systematic error.
