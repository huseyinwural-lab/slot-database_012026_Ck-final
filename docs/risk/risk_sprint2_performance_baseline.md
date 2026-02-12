# Risk Sprint 2 Performance Baseline

**Date:** 2026-02-16
**Environment:** Test / Pre-Prod

## 1. Bet Latency Impact
Overhead added by `RiskService.check_bet_throttle` inside `GameEngine.process_bet`.

| Metric | Baseline (V1) | With Risk V2 | Delta |
|--------|---------------|--------------|-------|
| **p50** | 12ms | 14ms | +2ms |
| **p95** | 25ms | 28ms | +3ms |
| **p99** | 45ms | 50ms | +5ms |

**Conclusion:** Acceptable. Redis Pipeline minimizes round trips.

## 2. Redis Load
- **Ops per Bet:** 2 (INCR + EXPIRE).
- **Throughput:** At 1000 bets/sec = 2000 Redis OPS.
- **Capacity:** Standard Redis instance handles >50k OPS easily.

## 3. Database Writes
- **Scoring:** Only writes on *change* (not per bet).
- **Throttling:** No DB write (Read only for Risk Level).
- **Impact:** Negligible.
