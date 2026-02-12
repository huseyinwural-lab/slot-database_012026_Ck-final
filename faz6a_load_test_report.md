# Faz 6A Load Test Report (Plan)

**Target:** 1000 TPS
**Scenario:** Mixed Workload (70% Bet, 25% Win, 5% Rollback)

## 1. Environment
- **DB:** Production-grade PostgreSQL (or high-spec Test instance).
- **App:** 3+ Replicas.
- **Redis:** Clustered or High-Availability.

## 2. Execution Plan
1.  **Warmup:** 100 TPS for 5 mins.
2.  **Ramp:** 100 -> 1000 TPS over 10 mins.
3.  **Sustain:** 1000 TPS for 15 mins.
4.  **Cool down:** 100 TPS for 5 mins.

## 3. Metrics to Capture
- **Latency:** p50, p95, p99.
- **Throughput:** Requests per second.
- **Errors:** 5xx rate.
- **Resources:** CPU, Memory, DB Connections.

## 4. Success Criteria
- [ ] No Duplicate Settlements.
- [ ] No Wallet Drift.
- [ ] Error Rate < 0.1%.
- [ ] p95 Latency < 500ms.
