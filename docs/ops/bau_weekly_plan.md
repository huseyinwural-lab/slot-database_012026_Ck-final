# BAU Sprint 1: Weekly Operational Plan

**Period:** Week 1 Post-Go-Live
**Owner:** Solo Dev/Ops
**Focus:** Stability & Automation

## 1. Routine Automation (P1)
- [ ] **Daily Health Summary:** Automate `hc_010_health.py` via Cron to email/slack a daily summary at 08:00 UTC.
- [ ] **Log Rotation:** Verify `logrotate` is active for application logs to prevent disk saturation.

## 2. KPI & SLO Dashboarding (P1)
- [ ] **Finance Dashboard:**
  - Implement query for `Deposit Success Rate` (Last 24h).
  - Implement query for `Withdrawal Processing Time` (Avg).
- [ ] **Integrity Dashboard:**
  - Add `Audit Chain Verification Status` (Last Run Result).

## 3. "Break-Glass" Drills (P2)
- [ ] **DB Restore:** Perform one restore to a staging environment to validate the 15-minute RTO target.
- [ ] **Audit Rehydration:** Restore a random day from S3 to a temporary analysis DB to verify manifest integrity.

## 4. Engine Standards Maintenance (P2)
- [ ] **Audit Review:** Review all `ENGINE_CONFIG_UPDATE` events from Week 0.
- [ ] **Rule Tuning:** If any "Review Required" events were false positives, adjust `is_dangerous_change` logic.

## 5. Security & Access
- [ ] **Key Rotation:** Schedule first rotation of `JWT_SECRET` (if policy dictates monthly).
- [ ] **Access Audit:** List all active sessions and invalidate any stale Admin tokens.
