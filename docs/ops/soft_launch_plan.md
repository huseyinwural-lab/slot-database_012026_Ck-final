# Soft Launch Plan (7 Days)

**Objective:** Gradual ramp-up to validate stability and financial integrity.

## Days 1-2: Low Limit / Internal
- **Config:**
    -   Max Bet Limit: Low ($10 - $50).
    -   Features: Bonus OFF, Progressives OFF.
- **Process:**
    -   Manual Reconciliation runs every 6 hours.
    -   Daily Metric Snapshot review.

## Days 3-4: Ramp Up
- **Config:**
    -   Increase Limits slightly.
    -   Enable standard promotions.
- **Analysis:**
    -   Check Callback Latency Trend (drift?).
    -   Monitor `provider_duplicate_callbacks_total`.
    -   Review Risk Block patterns (tuning rules).

## Days 5-7: Stability & Automation
- **Checks:**
    -   Is Reconciliation running automatically?
    -   Is Drift Trend flat (0.00)?
    -   Error Rate < 0.1%?
    -   CPU/Memory baselines established?

## Success Criteria (Day 7)
- No unexplained financial drift.
- No critical incidents.
- Operational confidence to remove "Soft" tag.
