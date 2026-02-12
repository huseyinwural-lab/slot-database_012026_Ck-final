# Faz 6A Sprint 2 Observability Report

**Status:** ACTIVE
**Date:** 2026-02-16

## 1. Metrics Added
- `provider_requests_total`: Tracks raw callback volume.
- `provider_signature_failures_total`: Tracks auth failures.
- `provider_duplicate_callbacks_total`: Tracks idempotency hits (To be implemented in Adapter/Router).
- `provider_wallet_drift_detected_total`: From Reconciliation Job.

## 2. Alerts Configured
- **High Error Rate:** > 5% failure on callbacks.
- **Drift Critical:** Any drift > 0.01 triggers PagerDuty.
- **Latency Warning:** p99 > 500ms.

## 3. Logs
- Structured logs in `GameEngine` and `GamesCallbackRouter` allow tracing `provider_tx_id` through the system.
