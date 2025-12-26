# Post-Go-Live Backlog (Stabilization Phase)

**Status:** P1 (Next Sprints)
**Owner:** Product & Ops

## 1. Monitoring & Tuning
- [ ] **Alert Tuning:** Review alert noise after W1. Adjust thresholds for 5xx and latency.
- [ ] **DB Performance:** Analyze slow queries (pg_stat_statements) after W2 load. Add indexes.
- [ ] **Queue Optimization:** Tune worker concurrency for Reconciliation/Archival if laggy.

## 2. Integrations
- [ ] **Live Providers:** Activate Real Payment Providers (Stripe/Adyen Live Mode) one by one.
- [ ] **Game Aggregator:** Integrate real game provider (Evolution/Pragmatic) replacing internal mock.

## 3. Fraud & Risk
- [ ] **Velocity Rules:** Tighten deposit limits based on actual abuse patterns.
- [ ] **Bonus Abuse:** Implement device fingerprinting logic (if not fully active).

## 4. Compliance (Day 30+)
- [ ] **External Audit Prep:** Generate full month audit dump for external auditors.
- [ ] **GDPR/KVKK:** Automate "Right to be Forgotten" (Data Anonymization script).

## 5. Feature Enhancements
- [ ] **Advanced CRM:** Segment-based bonus targeting.
- [ ] **Affiliate Portal:** Self-service dashboard for affiliates.
