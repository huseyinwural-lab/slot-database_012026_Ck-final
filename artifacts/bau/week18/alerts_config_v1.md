# Alerts Config v1

## Overview
This configuration defines the alert rules monitored by the `AlertEngine`.
Since we are in a containerized env without external Prometheus, `AlertEngine` runs periodically as a cron job.

## Alert Severity Levels
- **CRITICAL:** Immediate action required. Wake up on-call.
- **WARN:** Action required within business hours.
- **INFO:** For visibility and trends.

## Rules

### 1. Payment Success Rate (Critical)
- **Metric:** `success_rate` (completed / attempts) over last 15 mins.
- **Threshold:** < 80%
- **Severity:** CRITICAL
- **Query:** `SELECT count(*) FROM transaction WHERE created_at > NOW() - 15min`

### 2. Reconciliation Mismatch (Warn)
- **Metric:** `mismatch_count` (status='MISMATCH')
- **Threshold:** > 0 (Any mismatch is bad)
- **Severity:** WARN
- **Query:** `SELECT count(*) FROM reconciliation_findings WHERE status = 'OPEN'`

### 3. Risk / Collusion Spike (Info)
- **Metric:** `signal_count` (type='chip_dumping' OR 'collusion')
- **Threshold:** > 5 in last hour
- **Severity:** INFO
- **Query:** `SELECT count(*) FROM risksignal WHERE created_at > NOW() - 1h`

### 4. Dispute Rate Anomaly (Warn)
- **Metric:** `dispute_count` / `transaction_count` ratio
- **Threshold:** > 1% (Standard risk limit)
- **Severity:** WARN

## Notification Channels
- **Slack/Discord:** Webhook (Simulated via log output for now).
- **Email:** Admin email (Simulated).
