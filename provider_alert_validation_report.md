# Provider Alert Validation Report (Plan)

**Goal:** Verify all alert pipelines are active and routing correctly.

## 1. Scenarios
| Scenario | Action | Expected Alert | Channel |
|----------|--------|----------------|---------|
| **Signature Fail** | Send bad HMAC | `provider_signature_failures_total` > 0 | Warning |
| **Drift** | Manually edit ledger | `provider_wallet_drift_detected_total` > 0 | Critical |
| **Risk Block** | Burst High Risk Bets | `risk_blocks_total` Spike | Warning |
| **DB Down** | Stop DB Container | `provider_requests_total{status="system_error"}` | Critical |

## 2. Verification Steps
1.  Trigger event.
2.  Check Prometheus target.
3.  Check Alertmanager routing.
4.  Verify Slack/PagerDuty notification.
