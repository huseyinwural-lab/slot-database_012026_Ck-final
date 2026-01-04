# Go-Live Canary Report
**Execution Date:** ______________
**Executor:** __________________
**Environment:** PROD

## 1. Canary User Details
- **User ID:** ________________________________________
- **Email:** __________________________________________ (e.g. canary_prod_20251226@example.com)
- **KYC Status:** [ ] Verified (Manual Admin Override)

## 2. Money Loop Execution
| Step | Action | Expected | Actual Values | Tx ID / Ref | Result |
|---|---|---|---|---|---|
| 1 | **Deposit** ($10.00) | Balance: +10.00 | Avail: ______ | Tx: __________________ | [ ] PASS |
| 2 | **Withdraw Request** ($5.00) | Avail: -5.00 <br> Held: +5.00 | Avail: ______ <br> Held: ______ | Tx: __________________ | [ ] PASS |
| 3 | **Admin Approve** | State: 'Approved' | State: ______ | - | [ ] PASS |
| 4 | **Admin Payout** | State: 'Paid' / 'Payout Pending' | State: ______ | Ref: _________________ | [ ] PASS |
| 5 | **Ledger Settlement** | Held: 0.00 | Held: ______ | - | [ ] PASS |

## 3. Webhook Verification
- [ ] Deposit Webhook Received (Signature Verified)
- [ ] Payout Webhook Received (Signature Verified)
- [ ] Idempotency Check (Replay same webhook -> 200 OK, no double balance credit)

## 4. Final Decision
- **Canary Outcome:** [ ] GO / [ ] NO-GO
- **Blockers / Anomalies:**
  _________________________________________________________________________
  _________________________________________________________________________

**Signed:** ____________________
