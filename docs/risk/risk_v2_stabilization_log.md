# Risk V2 Stabilization Log

**Period:** 7 Days Post-Release
**Owner:** Risk Ops Team

## Daily Checklist

### Day 1-3 (Intensive)
- [ ] **Redis Latency:** Check `game_engine_latency_seconds`. Target p99 < 50ms.
- [ ] **Throttling Rate:** Check `bet_rate_limit_exceeded_total`. Is it blocking real players?
- [ ] **Withdrawal Friction:** Monitor `risk_flags_total`. Is the manual queue manageable?
- [ ] **Error Logs:** Grep for `Risk evaluation failed`.

### Day 4-7 (Tuning)
- [ ] **Score Distribution:** Verify Pareto distribution (90% Low, <2% High).
- [ ] **Override Analysis:** Are admins reverting specific rules often? (Indicates bad rule).
- [ ] **False Positives:** Review user tickets regarding "Unable to withdraw".

## Sign-off
- **Date:** [YYYY-MM-DD]
- **Status:** STABILIZED / ROLLBACK / HOTFIX NEEDED
