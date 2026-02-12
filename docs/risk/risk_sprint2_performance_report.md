# Risk Sprint 2 Performance Report

**Test:** Bet Burst Scenario
**Target:** < 5ms overhead for Risk Check.

## 1. Latency Analysis
- **Redis Check:** ~1-2ms (Pipeline: INCR + EXPIRE).
- **DB Check (Profile):** ~2-5ms (Cached by SQL Page Cache, but hits DB).
- **Total Overhead:** ~5-8ms.

## 2. Optimization Status
- **Current:** Fetch `RiskProfile` from DB on every Bet.
- **Optimization (P2):** Cache `RiskLevel` in Redis (`risk:level:{user_id}`) for 5 minutes.
- **Decision:** Accept 5ms overhead for Sprint 2 (MVP).

## 3. Throughput
- **Redis Capacity:** Handles >10k ops/sec.
- **Token Bucket:** efficient O(1) complexity.
