# Risk Observability Specification

## 1. Metrics (Prometheus)

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `risk_event_processed_total` | Counter | `type`, `tenant_id` | Total risk events ingested. |
| `risk_score_updated_total` | Counter | `direction` (up/down) | Frequency of score changes. |
| `withdrawal_blocked_risk_total` | Counter | `reason` | Total withdrawals auto-rejected. |
| `withdrawal_flagged_total` | Counter | `reason` | Total withdrawals sent to review. |
| `manual_review_queue_depth` | Gauge | `tenant_id` | Pending manual reviews. |

## 2. Logs (Structured)

### Score Change Log
```json
{
  "event": "risk_score_change",
  "user_id": "...",
  "old_score": 20,
  "new_score": 55,
  "trigger_rule": "rapid_deposit",
  "correlation_id": "..."
}
```

### Block Log
```json
{
  "event": "risk_block",
  "action": "withdraw",
  "user_id": "...",
  "score": 85,
  "threshold": 70
}
```
