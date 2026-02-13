# Production Deployment Checklist

**Status:** MANDATORY GATE
**Role:** DevOps / Tech Lead

## 1. Pre-Deploy Gate (GO / NO-GO)
All items must be CHECKED before starting deployment.

- [ ] **Soak Test:** PASS (72h stable in Staging).
- [ ] **Financial Integrity:** Drift = 0.00, Duplicate Settlement = 0.
- [ ] **Security:** `prod_guard.py` PASS.
- [ ] **Configuration:**
    - [ ] `DEBUG = false`
    - [ ] Secrets loaded via ENV (not hardcoded).
    - [ ] Provider Signature Key verified.
    - [ ] `allow_test_payment_methods = False`
    - [ ] `ledger_enforce_balance = True`
    - [ ] `webhook_signature_enforced = True`
- [ ] **Database:**
    - [ ] `alembic head` matches codebase.
    - [ ] Point-in-time Backup taken immediately before deploy.
- [ ] **Monitoring:** Alert channels (PagerDuty/Slack) active.
- [ ] **Frontend:**
    - [ ] No `console.log` in critical flows.
    - [ ] No 3rd party badges/scripts.

## 2. Deployment Sequence (30-45 Mins)
1.  **Maintenance Mode:** Enable (optional, depending on strategy).
2.  **Database:** Run `alembic upgrade head`.
3.  **Application:** Deploy Backend Containers.
4.  **Verification (Smoke):**
    - [ ] `GET /health` returns 200.
    - [ ] `GET /metrics` returns Prometheus data.
    - [ ] Manual Ping to Provider Callback Endpoint (expect 403 or specific error).
    - [ ] Admin Panel Login.
5.  **Live Test (Internal User):**
    - [ ] Place 1 Bet ($1.00).
    - [ ] Trigger 1 Win ($0.50).
    - [ ] Verify Wallet Balance.
6.  **Reconciliation:** Run manual `recon_provider.py` check.

## 3. Post-Deploy Watch (First 2 Hours)
- [ ] **Latency:** Monitor p95 < 200ms.
- [ ] **Traffic:** Watch `provider_requests_total`.
- [ ] **Risk:** Check for `risk_blocks_total` spikes (false positives?).
- [ ] **Resources:** DB Pool saturation & Redis Memory.
