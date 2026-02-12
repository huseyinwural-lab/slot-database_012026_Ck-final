# Risk Production Guardrails

## 1. Centralized Throttle Configuration
*(Currently hardcoded in `RiskService.check_bet_throttle` for MVP - Pending extraction to YAML/Env)*

### Config Values
| Level | Rate Limit (Bets/Min) | Burst |
|-------|-----------------------|-------|
| **LOW** | 60 | 10 |
| **MEDIUM** | 30 | 5 |
| **HIGH** | 10 | 0 |

## 2. Redis Key Namespace
**Standard Prefix:** `risk:`

| Purpose | Pattern | TTL |
|---------|---------|-----|
| Bet Velocity | `risk:throttle:bet:{user_id}:{minute}` | 65s |
| Deposit Count | `risk:velocity:dep_count:{user_id}:600` | 10m |
| Withdrawal Amt | `risk:velocity:wdraw_amt:{user_id}:86400` | 24h |

## 3. Metric Alerts

### A. Critical (PagerDuty)
- **`bet_rate_limit_exceeded_total` Spike:** > 1000/min. Indicates potential DDoS or broken game client.
- **`risk_override_total` Anomaly:** > 50/hour. Possible internal abuse.

### B. Warning (Slack)
- **`risk_score_updates_total` Zero:** System might be idle or broken.
- **Redis Connection Error:** Fallback mode active.

## 4. Operational Limits
- **Manual Override:** Requires valid reason string > 5 chars.
- **Expiry:** Max override duration recommended 7 days.
