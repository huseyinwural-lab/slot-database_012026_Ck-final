# On-Call Runbook

## Roles
- **Level 1 (Ops):** Monitor Dashboard, Handle refunds < $1000.
- **Level 2 (Dev):** Webhook failures, Payout stuck > 1 hour.

## Routine Checks
1. **Daily:** Check `/api/v1/ops/dashboard` for red flags.
2. **Daily:** Verify `ReconciliationRun` status is "success".

## Incident Response
### "Payout Stuck"
1. Query `Transaction` where `status='payout_pending'` and `updated_at < NOW() - 1 hour`.
2. Check `PayoutAttempt` for errors.
3. If `provider_ref` exists, check status in Adyen/Stripe Dashboard.
4. If Adyen says "Paid", manually update TX to `completed`.

### "Deposit Missing"
1. Ask user for `session_id` or date.
2. Search logs for that ID.
3. If found in logs but not DB, run `Reconciliation`.
