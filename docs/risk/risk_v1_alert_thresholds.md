# Risk V1 Alert Thresholds

**Goal:** Detect anomalies in risk engine behavior and operational bottlenecks.

## 1. Critical Alerts (P0)
| Metric | Threshold | Duration | Description | Action |
|--------|-----------|----------|-------------|--------|
| `withdraw_blocked_total` | > 100 | 1h | Surge in blocked withdrawals. Potential False Positive wave. | Check recent rule changes. |
| `risk_service_errors` | > 1% | 5m | Redis connectivity or DB issues. | Check Infra health. |

## 2. Operational Alerts (P1)
| Metric | Threshold | Duration | Description | Action |
|--------|-----------|----------|-------------|--------|
| `manual_review_queue_total` | > 50 | 4h | Backlog in soft-flagged withdrawals. | Alert Ops Team. |
| `risk_score_changed_total` | > 1000 | 1h | Unusual spike in risk events (Attack?). | Analyze IP patterns. |

## 3. Business Logic Alerts (P2)
| Metric | Threshold | Duration | Description | Action |
|--------|-----------|----------|-------------|--------|
| `risk_level_distribution` | High > 5% | 24h | Too many users classified as High Risk. | Review scoring weights. |

## 4. Implementation
Prometheus rules to be deployed to `monitoring` namespace.
