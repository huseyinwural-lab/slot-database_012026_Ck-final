# Alerting Rules & Thresholds (D4-2)

**Status:** ACTIVE
**Integration:** PagerDuty + Slack (`#ops-alerts`)

## 1. Critical Alerts (Page On-Call)

| Alert Name | Condition | Threshold | Response SLA |
|------------|-----------|-----------|--------------|
| **High Error Rate** | HTTP 5xx rate | > 5% for 5 mins | 15 mins |
| **DB Connection Saturation** | Active connections | > 80% pool size | 30 mins |
| **Audit Chain Failure** | `verify_audit_chain` | Fails (Integrity Error) | **IMMEDIATE** |
| **Payment Success Dip** | Successful Deposit Rate | Drop > 50% vs 1h avg | 30 mins |
| **Archive Job Failure** | Cron Job Exit Code | != 0 (Daily) | 2 hours |

## 2. Warning Alerts (Slack Only)

| Alert Name | Condition | Threshold |
|------------|-----------|-----------|
| **Latency Spike** | p95 Latency | > 500ms for 10 mins |
| **Recon Mismatch** | `reconciliation_findings` | count > 0 |
| **Disk Usage** | Volume utilization | > 80% |

## 3. Test Evidence
- **Simulation:** `d4_alert_test_evidence.txt` (Simulated 500 error spike trigger).
