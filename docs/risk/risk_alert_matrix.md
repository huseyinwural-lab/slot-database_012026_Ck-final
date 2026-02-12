# Risk Alert Matrix

**Severity Levels:**
- **INFO:** Routine operational events (e.g., successful block).
- **WARNING:** Potential issues requiring attention within 24h.
- **CRITICAL:** Immediate action required (Service degradation or massive abuse).

## 1. Alert Rules

| Metric | Condition | Severity | Description | Action |
|--------|-----------|----------|-------------|--------|
| `risk_blocks_total` | > 100 / hour | WARNING | Surge in blocked withdrawals. Possible false positive wave. | Check recent rule changes. |
| `risk_blocks_total` | > 1000 / hour | CRITICAL | Massive block wave. Likely DDoS or bug. | Investigate immediately. |
| `bet_rate_limit_exceeded_total` | > 5000 / min | CRITICAL | Bot attack detected on Game Engine. | Check IP limits / WAF. |
| `risk_override_total` | > 20 / hour | WARNING | High manual intervention rate. | Review Admin logs. |
| `risk_service_errors` | > 1% of reqs | CRITICAL | Risk Engine failing (Redis/DB). | Check Infrastructure. |

## 2. Notification Channels
- **CRITICAL:** PagerDuty + Slack `#ops-critical`
- **WARNING:** Slack `#risk-alerts`
- **INFO:** Dashboard Only
