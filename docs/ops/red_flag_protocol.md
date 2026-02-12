# Red Flag Protocol (Emergency Response)

**Trigger:** Immediate intervention required if ANY of the following occur.

## 1. The Red Flags
1.  **Financial Drift:** `Drift > 0.00` in Reconciliation.
2.  **Double Spend:** `Duplicate Settlement > 0`.
3.  **Latency Spike:** p95 jumps > 1s (Cascading failure risk).
4.  **Security Breach:** Signature Validation Failure Spike (> 10/min).
5.  **Infrastructure:** DB Lock Timeout or Connection Pool Exhaustion.

## 2. Immediate Actions (Playbook)

### Level 1: Financial Anomaly (Drift/Double Spend)
1.  **STOP:** Disable Provider Integration (Maintenance Mode or API Circuit Breaker).
2.  **AUDIT:** Identify the specific transaction IDs.
3.  **FIX:** Patch logic or data.
4.  **RESUME:** Only after 0 drift confirmed.

### Level 2: Performance (Latency/DB)
1.  **THROTTLE:** Reduce Bet Limits or Rate Limit via WAF/Gateway.
2.  **SCALE:** Increase Read Replicas or Redis Cluster size.

### Level 3: Security (Signature Fails)
1.  **BLOCK:** Block offending IPs at Firewall/Cloudflare.
2.  **ROTATE:** Rotate Provider Secret Keys immediately.

## 3. Contact Chain
1.  On-Call Engineer
2.  Tech Lead
3.  Head of Product (for business impact)
