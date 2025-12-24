# Go-Live Cutover Checklist

## 1. Environment & Secrets
- [ ] `ENV=prod` confirmed in deployment config.
- [ ] `STRIPE_SECRET_KEY` (Live) configured.
- [ ] `STRIPE_WEBHOOK_SECRET` (Live) configured.
- [ ] `ADYEN_API_KEY` (Live) configured.
- [ ] `ADYEN_MERCHANT_ACCOUNT` (Live) configured.
- [ ] `ADYEN_HMAC_KEY` (Live) configured.
- [ ] `ALLOW_TEST_PAYMENT_METHODS=false` confirmed.

- [ ] `PAYOUTS_ROUTER` active (Endpoint `/api/v1/payouts/initiate` reachable).
- [ ] Ledger Logic Verified (Withdrawal deducts balance immediately).
## 2. Infrastructure
- [ ] Database backup executed (Restore Drill PASS).
- [ ] Redis Queue (Reconciliation) running.
- [ ] Webhook Endpoints publicly accessible (SSL enabled).

## 3. Operations
- [ ] Payout Gating verified (Mock blocked).
- [ ] Dashboard accessible to Ops team.
- [ ] Alert channels (Slack/Email) configured.

## 4. Rollback Plan
**Trigger:**
- Payout Failure Rate > 15% for > 1 hour.
- Critical Security Incident (Webhook bypass).

**Steps:**
1. Switch `PAYOUT_PROVIDER` to `manual` (if supported) or disable withdrawals via `KILL_SWITCH_WITHDRAWALS`.
2. Revert Deployment to previous tag.
3. Notify Stakeholders.

## 5. SLA Minimums
- API Availability: 99.9%
- Payout Processing Time: < 24 hours (provider dependent)
- Support Ticket Response: < 4 hours
